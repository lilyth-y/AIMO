"""
로컬(또는 HF Hub) **실제 causal LM**으로 수학 답 품질 샘플 평가.

- 데이터·프롬프트·채점: `eval_vertex_endpoint_quality.py` 와 동일 계열
- 추론: `transformers` + `torch` (serve.py 와 유사한 generate 경로)

GCS/Vertex 없이도 **머지 디렉터리 로컬 경로** 또는 **HF 모델 ID** 로 평가를 시작할 수 있다.

사용 예:
  python scripts/eval_hf_local_quality.py --model Qwen/Qwen2.5-Math-1.5B-Instruct --n-problems 30
  python scripts/eval_hf_local_quality.py --model D:/path/to/merged --n-problems 50 --device cpu

결과: stdout JSON 요약(strict_format_compliance, accuracy, format_attempts 등) + results/hf_local_eval_<ts>.jsonl

형식 게이트: 단일 비어 있지 않은 <ANS> 블록이 나올 때까지 최대 (1+--max-format-retries)회 생성.
통과한 샘플만 정답 채점(scoring_status=graded).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from evaluation.config import RESULTS_DIR, ensure_dir, find_data_file, NUMINA_TRAINING_FILE  # noqa: E402
from evaluation.evaluation_utils import (  # noqa: E402
    classify_answer_match,
    determine_difficulty_from_source,
)
from evaluation.eval_grading import grade_completion_for_eval  # noqa: E402
from pipeline.answer_extraction import AnswerExtractor  # noqa: E402
from pipeline.ans_format_guard import (  # noqa: E402
    build_format_repair_prompt,
    build_prompt_strict_first,
    validate_ans_strict,
)


@dataclass
class ProblemItem:
    idx: int
    problem: str
    answer: str
    source: str


def _looks_non_numeric_answer(ans: Any) -> bool:
    if ans is None:
        return True
    s = str(ans).strip().lower()
    if not s:
        return True
    if s in {"proof", "prove", "proved", "true", "false"}:
        return True
    return False


def _json_safe(obj: Any) -> Any:
    """JSON 직렬화 가능한 값으로 변환 (SymPy, Ellipsis 등 방지)."""
    if obj is Ellipsis:
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    return str(obj)


def load_numina_jsonl_filtered(
    n: int,
    seed: int,
    filename: str = NUMINA_TRAINING_FILE,
) -> List[ProblemItem]:
    path = find_data_file(filename)
    rng = __import__("random").Random(seed)
    pool: List[ProblemItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            problem = obj.get("problem") or ""
            answer = obj.get("answer")
            source = obj.get("source") or "unknown"
            if not isinstance(problem, str) or not problem.strip():
                continue
            if _looks_non_numeric_answer(answer):
                continue
            pool.append(ProblemItem(idx=i, problem=problem, answer=str(answer), source=str(source)))
    if len(pool) < n:
        raise RuntimeError(f"요청 n={n}, 사용 가능={len(pool)} in {path}")
    rng.shuffle(pool)
    return pool[:n]


def _looks_like_explicit_local_path(s: str) -> bool:
    """Windows 드라이브·UNC·상대경로 등 ‘로컬 경로’로 보이는지."""
    t = s.strip()
    if len(t) >= 2 and t[1] == ":" and t[0].isalpha():
        return True
    if t.startswith(("\\\\", "/", "./", "../", ".\\", "..\\")):
        return True
    return False


def normalize_model_path(model: str) -> str:
    """
    HF Hub ID는 그대로 두고, 로컬 머지 디렉터리면 절대경로로 정규화·검증.
    디렉터리인 경우 config.json 존재 여부 확인.
    """
    raw = model.strip()
    p = Path(raw).expanduser()
    if p.is_file():
        raise RuntimeError(
            f"모델은 디렉터리(HF 포맷, config.json 포함)를 지정하세요: {raw}"
        )
    if p.is_dir():
        cfg = p / "config.json"
        if not cfg.is_file():
            raise RuntimeError(
                f"HF 모델 디렉터리에 config.json이 없습니다: {p.resolve()}"
            )
        return str(p.resolve())
    if _looks_like_explicit_local_path(raw) and not p.exists():
        raise RuntimeError(
            f"모델 경로를 찾을 수 없습니다: {raw}\n"
            "머지 루트(예: 학습 산출 merged/)를 확인하세요."
        )
    return raw


def completion_after_prompt(full_text: str, prompt: str) -> str:
    """generate 디코드 전체에서 프롬프트 이후(모델 연속 출력)만 잘라낸다."""
    if full_text.startswith(prompt):
        return full_text[len(prompt) :]
    idx = full_text.find(prompt)
    if idx >= 0:
        return full_text[idx + len(prompt) :]
    return full_text


def has_ans_tags(text: str) -> bool:
    """프롬프트 준수: <ANS>...</ANS> 쌍이 있는지(대소문자 무시)."""
    t = text.lower()
    return "<ans>" in t and "</ans>" in t


def _load_model_and_tokenizer(model_id: str, device_hint: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    if device_hint == "cpu":
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            dtype=torch.float32,
        )
        model = model.to("cpu")
    else:
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            dtype=dtype,
            device_map="auto",
        )
    model.eval()
    return model, tok


def _generate_text(model, tokenizer, prompt: str, max_new_tokens: int, temperature: float) -> str:
    import torch

    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    do_sample = temperature > 0.0
    gen_kw: Dict[str, Any] = {
        "max_new_tokens": int(max_new_tokens),
        "do_sample": do_sample,
        "pad_token_id": tokenizer.pad_token_id,
    }
    if do_sample:
        gen_kw["temperature"] = float(temperature)
    with torch.no_grad():
        out = model.generate(**inputs, **gen_kw)
    return tokenizer.decode(out[0], skip_special_tokens=True)


def generate_with_format_retries(
    model: Any,
    tokenizer: Any,
    problem: str,
    max_new_tokens: int,
    base_temperature: float,
    retry_temperature: float,
    max_format_retries: int,
) -> Dict[str, Any]:
    """
    형식 검증 통과할 때까지 최대 (1 + max_format_retries)회 생성.
    채점은 format_ok 일 때만 의미가 있다.
    """
    max_attempts = max(1, max_format_retries + 1)
    t_total = 0.0
    last_reason = "UNKNOWN"
    last_text = ""
    last_prompt = ""
    last_err: Optional[str] = None

    for attempt in range(max_attempts):
        if attempt == 0:
            prompt = build_prompt_strict_first(problem)
            temp = base_temperature
        else:
            prompt = build_format_repair_prompt(problem)
            # 첫 시도가 greedy(0)일 때 재시도는 약간 샘플링
            temp = float(retry_temperature) if retry_temperature > 0 else 0.1

        t0 = time.time()
        try:
            text = _generate_text(
                model,
                tokenizer,
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temp,
            )
            last_err = None
        except Exception as e:
            last_err = str(e)
            text = ""
        t_total += time.time() - t0

        if last_err is not None:
            return {
                "full_text": text,
                "prompt": prompt,
                "attempts": attempt + 1,
                "format_ok": False,
                "format_reason": f"generation_error:{last_err}",
                "completion": "",
                "latency_s": round(t_total, 3),
                "error": last_err,
            }

        comp = completion_after_prompt(text, prompt)
        validation = validate_ans_strict(comp)
        last_text = text
        last_prompt = prompt
        if validation.ok:
            return {
                "full_text": text,
                "prompt": prompt,
                "attempts": attempt + 1,
                "format_ok": True,
                "format_reason": None,
                "completion": comp,
                "latency_s": round(t_total, 3),
                "error": None,
            }
        last_reason = validation.reason or "UNKNOWN"

    return {
        "full_text": last_text,
        "prompt": last_prompt,
        "attempts": max_attempts,
        "format_ok": False,
        "format_reason": last_reason,
        "completion": completion_after_prompt(last_text, last_prompt),
        "latency_s": round(t_total, 3),
        "error": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="로컬/HF 실제 모델 수학 답 품질 평가")
    ap.add_argument(
        "--model",
        required=True,
        help="HuggingFace 모델 ID 또는 로컬 머지 디렉터리 경로",
    )
    ap.add_argument(
        "--n-problems",
        type=int,
        default=30,
        help="평가할 문제 수 (프롬프트 준수·정확도 통계 안정화를 위해 30~50 권장)",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--data-file", default=NUMINA_TRAINING_FILE)
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument(
        "--max-format-retries",
        type=int,
        default=3,
        help="형식(<ANS> 단일·비어 있지 않음) 불통과 시 재생성 횟수. 0이면 1회만.",
    )
    ap.add_argument(
        "--retry-temperature",
        type=float,
        default=0.35,
        help="재시도 시 샘플링 온도(첫 시도는 --temperature).",
    )
    ap.add_argument(
        "--device",
        choices=("auto", "cpu"),
        default="auto",
        help="auto: CUDA 있으면 GPU. cpu: 강제 CPU(소형 실험용)",
    )
    ap.add_argument("--output", default="", help="JSONL 경로 (기본: results/hf_local_eval_<ts>.jsonl)")
    args = ap.parse_args()

    out_path = args.output
    if not out_path:
        ts = time.strftime("%Y%m%d_%H%M%S")
        ensure_dir(RESULTS_DIR)
        out_path = str(RESULTS_DIR / f"hf_local_eval_{ts}.jsonl")

    problems = load_numina_jsonl_filtered(args.n_problems, args.seed, filename=args.data_file)

    model_path = normalize_model_path(args.model)
    print(f"Loading model: {model_path!r} (device={args.device})...", flush=True)
    model, tokenizer = _load_model_and_tokenizer(model_path, args.device)
    extractor = AnswerExtractor()

    correct = 0
    ans_tag_ok = 0
    strict_ok = 0
    predicted_nonempty = 0
    total_attempts = 0
    rows: List[Dict[str, Any]] = []
    match_breakdown: Dict[str, int] = {
        "strict": 0,
        "sympy": 0,
        "numeric": 0,
        "ratio": 0,
        "interval": 0,
        "none": 0,
    }
    scoring_status_counts: Dict[str, int] = {}
    extraction_route_counts: Dict[str, int] = {}
    nonempty_raw_predicted_null = 0

    try:
        from tqdm import tqdm

        it = tqdm(problems, desc="hf_eval")
    except Exception:
        it = problems

    with open(out_path, "w", encoding="utf-8") as out_f:
        for j, p in enumerate(it):
            gen = generate_with_format_retries(
                model,
                tokenizer,
                p.problem,
                max_new_tokens=args.max_new_tokens,
                base_temperature=args.temperature,
                retry_temperature=args.retry_temperature,
                max_format_retries=args.max_format_retries,
            )
            text = gen["full_text"]
            prompt = gen["prompt"]
            dt = float(gen["latency_s"])
            err = gen.get("error")
            fmt_ok = bool(gen["format_ok"])
            total_attempts += int(gen["attempts"])

            if err:
                pred_str = None
                ok = False
                scoring_status = "skipped_invalid_format"
                ext_d = {
                    "value": None,
                    "format": "SKIPPED",
                    "confidence": 0.0,
                    "error": None,
                    "extraction_route": "skipped",
                }
            else:
                pred_str, ok, scoring_status, ext_d = grade_completion_for_eval(
                    p.answer,
                    text,
                    format_ok=fmt_ok,
                    fallback_boxed=False,
                    last_resort=False,
                    extractor=extractor,
                )
            pred_val = ext_d.get("value")

            if ok:
                correct += 1

            mk = classify_answer_match(p.answer, pred_str) if pred_str else "none"
            match_breakdown[mk] = match_breakdown.get(mk, 0) + 1

            scoring_status_counts[scoring_status] = scoring_status_counts.get(scoring_status, 0) + 1
            route = ext_d.get("extraction_route")
            if route:
                extraction_route_counts[route] = extraction_route_counts.get(route, 0) + 1
            if pred_str is None and (text or "").strip() and not err:
                nonempty_raw_predicted_null += 1

            comp = completion_after_prompt(text or "", prompt)
            ans_ok = has_ans_tags(comp)
            if ans_ok:
                ans_tag_ok += 1
            if fmt_ok:
                strict_ok += 1
            if pred_str is not None:
                predicted_nonempty += 1

            row = {
                "sample_idx": j,
                "problem_id": p.idx,
                "source": p.source,
                "difficulty": determine_difficulty_from_source(p.source),
                "reference_answer": p.answer,
                "latency_s": round(dt, 3),
                "error": err,
                "format_ok": fmt_ok,
                "format_attempts": gen["attempts"],
                "format_failure_reason": gen["format_reason"],
                "scoring_status": scoring_status,
                "extraction_route": ext_d.get("extraction_route"),
                "raw_text_head": (text[:1200] if text else ""),
                "completion_head": (comp[:800] if comp else ""),
                "has_ans_tags": ans_ok,
                "strict_format_ok": fmt_ok,
                "extracted": {
                    "value": pred_val,
                    "format": ext_d.get("format"),
                    "confidence": ext_d.get("confidence"),
                    "error": ext_d.get("error"),
                },
                "predicted_answer": pred_str,
                "is_correct": ok,
                "match_kind": mk,
            }
            rows.append(row)
            out_f.write(json.dumps(_json_safe(row), ensure_ascii=False) + "\n")

    n = len(rows)
    predicted_null = sum(1 for r in rows if r.get("predicted_answer") is None)
    summary = {
        "model": model_path,
        "model_arg": args.model,
        "n_problems": n,
        "correct": correct,
        "accuracy": correct / n if n else 0.0,
        "match_kind_breakdown": match_breakdown,
        "scoring_status_breakdown": scoring_status_counts,
        "extraction_route_breakdown": extraction_route_counts,
        "predicted_null_count": predicted_null,
        "predicted_null_rate": (predicted_null / n if n else 0.0),
        "nonempty_raw_predicted_null_count": nonempty_raw_predicted_null,
        "nonempty_raw_predicted_null_rate": (
            nonempty_raw_predicted_null / n if n else 0.0
        ),
        "ans_tag_compliance": {
            "with_ans_tags": ans_tag_ok,
            "rate": ans_tag_ok / n if n else 0.0,
        },
        "strict_format_compliance": {
            "passed": strict_ok,
            "rate": strict_ok / n if n else 0.0,
        },
        "format_attempts": {
            "total": total_attempts,
            "mean_per_problem": total_attempts / n if n else 0.0,
            "max_format_retries": args.max_format_retries,
        },
        "predicted_nonnull": {
            "count": predicted_nonempty,
            "rate": predicted_nonempty / n if n else 0.0,
        },
        "seed": args.seed,
        "data_file": args.data_file,
        "device": args.device,
        "output": out_path,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
