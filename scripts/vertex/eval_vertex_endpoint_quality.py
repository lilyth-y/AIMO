"""
Vertex Online Prediction 엔드포인트에 대해 **답 품질(정확도)** 샘플 평가.

- 데이터: `evaluation.config` 의 Numina JSONL (기본 `numina_training_5k.jsonl`에서 숫자 답만 필터)
- 채점: `evaluation.eval_grading.grade_completion_for_eval` + `classify_answer_match` (기존 파이프라인과 동일 계열)
- 추론: `google.cloud.aiplatform.Endpoint.predict` (serve.py 프로토콜: prompt / max_new_tokens / temperature; 기본 생성 8192, env `VERTEX_MAX_NEW_TOKENS`). SDK 타임아웃 상한 기본 **600초**(`VERTEX_PREDICT_TIMEOUT_MAX` / `--predict-timeout`). 503/지연 등은 `--vertex-predict-retries`(기본 3)와 `--vertex-predict-retry-delay`(초, 선형 백오프)로 재시도. 실패 시 JSONL `predict_progress`에 형식 라운드·재시도별 `predict_calls` 기록.
- 형식: `ans_format_guard` — `build_prompt_strict_first` + 실패 시 `build_format_repair_prompt` 재시도 (`--max-format-retries`). 서버는 생성만 반환하므로 strict 검증은 생성문 전체에 적용.
- 완화: 형식 미통과 시 `--fallback-boxed`(기본 on)로 마지막 `\\boxed{...}` 를 보조 추출. 선택 `--last-resort-extraction`(기본 off)로 tail 휴리스틱.
- 검수 Agent: 위로도 답이 없으면(또는 strict ANS는 있는데 파싱 실패) **동일 엔드포인트**에
  `build_verification_agent_prompt` 로 1회 추가 predict → `<ANS>` 정리본으로 재채점(`graded_verify_agent`).
  끄기: `--no-verify-agent` 또는 `VERTEX_VERIFY_AGENT=0`.
- BigQuery: `--bq-table project.dataset.table` 로 eval 종료 후 JSONL 행을 동일 run_id로 적재.
  `vertex_bigquery.py` + `pip install -r requirements-vertex-bq.txt`. 자동 생성: 기본 on, 끄기 `--bq-no-create`.

사용 예:
  set PROJECT_ID=...
  set LOCATION=asia-northeast3
  python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id 7467375001482559488 --n-problems 20

쉬운 벤치(정확도 확인용): 전체 Numina JSONL에서 소스 필터 — `numinamath_full.jsonl` 권장.
  python scripts/vertex/eval_vertex_endpoint_quality.py --endpoint-id ... ^
    --data-file numinamath_full.jsonl --sources orca_math,cn_k12 --difficulty-at-most medium --n-problems 15

결과: stdout 요약 + `--output` JSONL (문제별 raw/추출/정오답, `extraction_route`·`scoring_status_breakdown` 등 KPI).

로컬 진단: `python scripts/vertex/diagnose_vertex_eval_jsonl.py <jsonl>` 또는
`--compare 레거시.jsonl 게이트.jsonl` 로 형식 필드·<ANS> 휴리스틱 비교.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# 프로젝트 루트 → src (evaluation, pipeline)
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import resolve_location, resolve_project_id  # noqa: E402

from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_TRAINING_FILE  # noqa: E402
from evaluation.evaluation_utils import (  # noqa: E402
    classify_answer_match,
    determine_difficulty_from_source,
)
from evaluation.eval_grading import grade_completion_for_eval  # noqa: E402
from pipeline.answer_extraction import AnswerExtractor  # noqa: E402
from pipeline.ans_format_guard import (  # noqa: E402
    build_format_repair_prompt,
    build_prompt_strict_first,
    build_verification_agent_prompt,
    validate_ans_strict,
)

# docs/vertex/STEP2_QUALITY_GATES.md — `--enforce-gates`와 동기화
STEP2_MIN_PROBLEMS = 50
STEP2_MIN_STRICT_FORMAT_RATE = 0.98
STEP2_MIN_ACCURACY = 0.20
STEP2_MAX_PREDICTED_NULL_RATE = 0.20
STEP2_MAX_API_ERROR_RATE = 0.05


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


def _difficulty_rank(label: str) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(label, 1)


def _parse_sources_csv(s: str) -> Set[str]:
    out: Set[str] = set()
    for part in (s or "").split(","):
        p = part.strip().lower()
        if p:
            out.add(p)
    return out


def load_numina_jsonl_filtered(
    n: int,
    seed: int,
    filename: str = NUMINA_TRAINING_FILE,
    *,
    sources_allowlist: Optional[Set[str]] = None,
    difficulty_at_most: Optional[str] = None,
) -> List[ProblemItem]:
    path = find_data_file(filename)
    rng = __import__("random").Random(seed)
    pool: List[ProblemItem] = []
    # Diagnostics so Cloud Shell users can see why pool is empty.
    stats: Dict[str, int] = {
        "lines_total": 0,
        "lines_empty": 0,
        "json_parse_fail": 0,
        "missing_problem": 0,
        "filtered_non_numeric_answer": 0,
        "filtered_source_allowlist": 0,
        "filtered_difficulty_cap": 0,
        "accepted": 0,
    }
    src_counts: Dict[str, int] = {}
    src_kept: Dict[str, int] = {}
    cap: Optional[str] = None
    if difficulty_at_most:
        cap = difficulty_at_most.strip().lower()
        if cap not in ("easy", "medium", "hard"):
            raise ValueError(f"difficulty-at-most must be easy|medium|hard, got {difficulty_at_most!r}")
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            stats["lines_total"] += 1
            line = line.strip()
            if not line:
                stats["lines_empty"] += 1
                continue
            try:
                obj = json.loads(line)
            except Exception:
                stats["json_parse_fail"] += 1
                continue
            problem = obj.get("problem") or ""
            answer = obj.get("answer")
            source_raw = obj.get("source") or "unknown"
            src_norm = str(source_raw).strip().lower()
            src_counts[src_norm] = src_counts.get(src_norm, 0) + 1
            if not isinstance(problem, str) or not problem.strip():
                stats["missing_problem"] += 1
                continue
            if _looks_non_numeric_answer(answer):
                stats["filtered_non_numeric_answer"] += 1
                continue
            if sources_allowlist is not None and len(sources_allowlist) > 0:
                if src_norm not in sources_allowlist:
                    stats["filtered_source_allowlist"] += 1
                    continue
            if cap is not None:
                d = determine_difficulty_from_source(src_norm)
                if _difficulty_rank(d) > _difficulty_rank(cap):
                    stats["filtered_difficulty_cap"] += 1
                    continue
            pool.append(ProblemItem(idx=i, problem=problem, answer=str(answer), source=str(source_raw)))
            src_kept[src_norm] = src_kept.get(src_norm, 0) + 1
            stats["accepted"] += 1
    if len(pool) < n:
        # Show top sources to make it obvious when e.g. all are 'olympiads' (hard).
        top_src = sorted(src_counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
        top_kept = sorted(src_kept.items(), key=lambda kv: kv[1], reverse=True)[:10]
        detail = {
            "file": str(path),
            "requested_n": n,
            "available": len(pool),
            "difficulty_at_most": cap,
            "sources_allowlist": sorted(list(sources_allowlist))[:20] if sources_allowlist else [],
            "stats": stats,
            "top_sources_total": top_src,
            "top_sources_kept": top_kept,
            "hint": (
                "Pool is empty often because --difficulty-at-most filters out all sources "
                "(e.g. 'olympiads' => hard). Try removing --difficulty-at-most or set it to hard, "
                "or pass --sources to target easy/medium sources."
            ),
        }
        raise RuntimeError(
            f"요청 n={n}, 사용 가능={len(pool)} in {path}\n"
            + json.dumps(detail, ensure_ascii=False, indent=2)
        )
    rng.shuffle(pool)
    return pool[:n]


def build_prompt_legacy(problem_text: str) -> str:
    """형식 게이트 비활성화 시에만 사용 (구버전 호환)."""
    return (
        "You are solving a math problem. "
        "Return ONLY the final answer wrapped in <ANS>...</ANS>.\n"
        "No explanation, no code.\n\n"
        f"Problem:\n{problem_text.strip()}\n"
    )


def _prediction_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, dict):
        return str(raw.get("text", "") or "")
    return str(raw)


def _default_max_new_tokens() -> int:
    """env VERTEX_MAX_NEW_TOKENS: 미설정→8192, 0/none/unlimited/max→서버가 컨텍스트만큼."""
    v = os.getenv("VERTEX_MAX_NEW_TOKENS")
    if v is None or str(v).strip() == "":
        return 8192
    s = str(v).strip().lower()
    if s in ("0", "none", "unlimited", "max"):
        return 0
    return int(s)


def _predict_timeout_max_cap() -> float:
    """SDK predict 상한(초). 기본 600 — Vertex 게이트웨이·엔드포인트 응답 한도와 맞춤."""
    return float(os.getenv("VERTEX_PREDICT_TIMEOUT_MAX", "600"))


def _effective_predict_timeout(raw: float) -> float:
    """
    Endpoint.predict(timeout=None) 또는 매우 짧은 값은 gRPC 쪽에서 ~60초 전후로 끊겨
    503 \"Took too long to respond\" 처럼 보인다. 항상 충분한 초 단위를 넘긴다.
    최종값은 VERTEX_PREDICT_TIMEOUT_MAX(기본 600)으로 상한.
    """
    max_cap = _predict_timeout_max_cap()
    floor = float(os.getenv("VERTEX_PREDICT_TIMEOUT_FLOOR", "600"))
    # gRPC 기본(~60초)로 떨어지지만 않게 기본 최소를 90초로 둔다.
    # (짧은 스모크에서 120 같은 값을 허용하기 위해 300처럼 크게 두지 않는다.)
    minimum = float(os.getenv("VERTEX_PREDICT_TIMEOUT_MIN", "90"))
    if raw <= 0:
        r0 = min(floor, max_cap) if max_cap > 0 else floor
        sys.stderr.write(
            f"[vertex_eval] predict timeout={raw!r} → {r0}s "
            f"(<=0은 SDK에 전달 시 gRPC 기본 ~60초 한도; VERTEX_PREDICT_TIMEOUT_FLOOR)\n"
        )
        return r0
    r = float(raw)
    if r < minimum:
        sys.stderr.write(
            f"[vertex_eval] predict timeout {r}s < min {minimum}s → {minimum}s "
            f"(VERTEX_PREDICT_TIMEOUT_MIN)\n"
        )
        r = minimum
    if max_cap > 0 and r > max_cap:
        sys.stderr.write(
            f"[vertex_eval] predict timeout {r}s > max {max_cap}s → {max_cap}s "
            f"(VERTEX_PREDICT_TIMEOUT_MAX)\n"
        )
        r = max_cap
    return r


def _is_transient_vertex_predict_error(msg: str) -> bool:
    """503/지연/과부하 등 짧은 재시도로 회복될 수 있는 오류."""
    s = (msg or "").lower()
    needles = (
        "503",
        "429",
        "took too long",
        "unavailable",
        "deadline exceeded",
        "resource exhausted",
        "timeout",
        "temporarily",
    )
    return any(n in s for n in needles)


def _endpoint_predict_with_retries(
    endpoint: Any,
    instances: List[Dict[str, Any]],
    predict_timeout: float,
    *,
    transient_retries: int,
    retry_delay_s: float,
) -> tuple[Optional[Any], Optional[str], List[Dict[str, Any]]]:
    """endpoint.predict 를 일시 오류 시 재시도. trace: 각 SDK 호출별 ok/error/latency."""
    last_err: Optional[str] = None
    trace: List[Dict[str, Any]] = []
    n = max(1, int(transient_retries))
    for attempt in range(n):
        t0 = time.time()
        try:
            # Some google-cloud-aiplatform versions don't accept `timeout=` on Endpoint.predict.
            # Prefer passing it, but fall back to default if the SDK rejects the kwarg.
            try:
                resp = endpoint.predict(instances=instances, timeout=predict_timeout)
            except TypeError as e:
                msg = str(e)
                if "timeout" in msg and ("unexpected" in msg or "got an unexpected keyword" in msg):
                    resp = endpoint.predict(instances=instances)
                else:
                    raise
            dt = time.time() - t0
            trace.append(
                {
                    "transient_sub": attempt + 1,
                    "ok": True,
                    "error": None,
                    "latency_s": round(dt, 3),
                }
            )
            return resp, None, trace
        except Exception as e:
            last_err = str(e)
            dt = time.time() - t0
            trace.append(
                {
                    "transient_sub": attempt + 1,
                    "ok": False,
                    "error": last_err,
                    "latency_s": round(dt, 3),
                }
            )
            if attempt < n - 1 and _is_transient_vertex_predict_error(last_err):
                time.sleep(retry_delay_s * (attempt + 1))
                continue
            break
    return None, last_err, trace


def vertex_predict_with_format_retries(
    endpoint: Any,
    problem_text: str,
    *,
    max_new_tokens: int,
    base_temperature: float,
    retry_temperature: float,
    max_format_retries: int,
    predict_timeout: float,
    transient_retries: int = 3,
    retry_delay_s: float = 5.0,
) -> Dict[str, Any]:
    """
    <ANS> 단일 블록 strict 통과할 때까지 최대 (1 + max_format_retries)회 Vertex predict.
    응답은 서빙에서 생성분만 오므로 validate_ans_strict(전체 텍스트) 적용.
    """
    max_attempts = max(1, max_format_retries + 1)
    t_total = 0.0
    last_text = ""
    last_prompt = ""
    last_reason = "UNKNOWN"
    last_err: Optional[str] = None
    last_trace: List[Dict[str, Any]] = []

    for attempt in range(max_attempts):
        if attempt == 0:
            prompt = build_prompt_strict_first(problem_text)
            temp = base_temperature
            kind = "strict_first"
        else:
            prompt = build_format_repair_prompt(problem_text)
            temp = float(retry_temperature) if retry_temperature > 0 else 0.1
            kind = "repair"

        t0 = time.time()
        resp, pred_err, ptrace = _endpoint_predict_with_retries(
            endpoint,
            [
                {
                    "prompt": prompt,
                    "max_new_tokens": max_new_tokens,
                    "temperature": temp,
                }
            ],
            predict_timeout,
            transient_retries=transient_retries,
            retry_delay_s=retry_delay_s,
        )
        t_elapsed = time.time() - t0
        t_total += t_elapsed
        last_trace = ptrace
        if pred_err is not None:
            last_err = pred_err
            text = ""
        else:
            preds = getattr(resp, "predictions", None) or []
            raw = preds[0] if preds else None
            text = _prediction_text(raw)
            last_err = None

        last_prompt = prompt
        if last_err is not None:
            calls = [
                {**c, "format_attempt": attempt + 1, "format_attempt_kind": kind}
                for c in ptrace
            ]
            return {
                "text": text,
                "prompt_used": last_prompt,
                "attempts": attempt + 1,
                "format_ok": False,
                "format_reason": f"api_error:{last_err}",
                "latency_s": round(t_total, 3),
                "error": last_err,
                "predict_progress": {
                    "failed_at": "format_gate",
                    "outcome": "api_error",
                    "format_attempt_index": attempt + 1,
                    "format_attempt_kind": kind,
                    "format_attempts_planned": max_attempts,
                    "transient_retries_configured": transient_retries,
                    "predict_timeout_s": predict_timeout,
                    "predict_calls": calls,
                },
            }

        completion = text or ""
        validation = validate_ans_strict(completion)
        last_text = text
        if validation.ok:
            return {
                "text": text,
                "prompt_used": last_prompt,
                "attempts": attempt + 1,
                "format_ok": True,
                "format_reason": None,
                "latency_s": round(t_total, 3),
                "error": None,
            }
        last_reason = validation.reason or "UNKNOWN"

    last_kind = "strict_first" if max_attempts <= 1 else "repair"
    calls = [
        {**c, "format_attempt": max_attempts, "format_attempt_kind": last_kind}
        for c in last_trace
    ]
    return {
        "text": last_text,
        "prompt_used": last_prompt,
        "attempts": max_attempts,
        "format_ok": False,
        "format_reason": last_reason,
        "latency_s": round(t_total, 3),
        "error": None,
        "predict_progress": {
            "failed_at": "format_gate",
            "outcome": "format_validation_failed",
            "format_attempt_index": max_attempts,
            "format_attempt_kind": "repair",
            "format_attempts_planned": max_attempts,
            "transient_retries_configured": transient_retries,
            "predict_timeout_s": predict_timeout,
            "last_validation_reason": last_reason,
            "predict_calls": calls,
        },
    }


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _run_verification_agent(
    endpoint: Any,
    *,
    problem_text: str,
    raw_text: str,
    max_new_tokens: int,
    temperature: float,
    predict_timeout: float,
    transient_retries: int = 3,
    retry_delay_s: float = 5.0,
) -> Dict[str, Any]:
    """
    형식 미준수·추출 실패 시 동일 엔드포인트에 검수(정리) 1회 호출.
    응답 전체에 대해 validate_ans_strict 적용.
    """
    prompt = build_verification_agent_prompt(problem_text, raw_text)
    t0 = time.time()
    resp, pred_err, ptrace = _endpoint_predict_with_retries(
        endpoint,
        [
            {
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
            }
        ],
        predict_timeout,
        transient_retries=transient_retries,
        retry_delay_s=retry_delay_s,
    )
    if pred_err is not None:
        text = ""
        err = pred_err
    else:
        preds = getattr(resp, "predictions", None) or []
        raw = preds[0] if preds else None
        text = _prediction_text(raw)
        err = None
    dt = time.time() - t0
    completion = text or ""
    validation = validate_ans_strict(completion)
    vprog: Optional[Dict[str, Any]] = None
    if err is not None:
        vprog = {
            "failed_at": "verify_agent",
            "outcome": "api_error",
            "transient_retries_configured": transient_retries,
            "predict_timeout_s": predict_timeout,
            "predict_calls": [{**c, "stage": "verify_agent"} for c in ptrace],
        }
    return {
        "text": text,
        "prompt_used": prompt,
        "latency_s": round(dt, 3),
        "error": err,
        "format_ok": bool(validation.ok) and err is None,
        "format_reason": validation.reason if not validation.ok else None,
        "predict_progress": vprog,
    }


def _verify_agent_row(block: Dict[str, Any]) -> Dict[str, Any]:
    """JSONL용: 프롬프트 전체 대신 길이·응답 앞부분만."""
    out = {k: v for k, v in block.items() if k != "prompt_used"}
    pu = block.get("prompt_used")
    if isinstance(pu, str):
        out["prompt_char_len"] = len(pu)
    out["verify_text_head"] = (block.get("text") or "")[:800]
    return out


def _step2_gate_check(summary: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """
    STEP2_QUALITY_GATES.md 고정 임계값과 비교.
    api_error 비율 = (api_error + verify_api_error) / n_problems
    """
    n = int(summary.get("n_problems") or 0)
    strict_r = float(summary.get("strict_format_rate") or 0.0)
    acc = float(summary.get("accuracy") or 0.0)
    null_r = float(summary.get("predicted_null_rate") or 0.0)
    ss = summary.get("scoring_status_breakdown") or {}
    api_n = int(ss.get("api_error", 0)) if isinstance(ss, dict) else 0
    vfy_n = int(ss.get("verify_api_error", 0)) if isinstance(ss, dict) else 0
    api_total = api_n + vfy_n
    api_r = (api_total / n) if n else 0.0

    failures: List[str] = []
    if n < STEP2_MIN_PROBLEMS:
        failures.append(f"n_problems>={STEP2_MIN_PROBLEMS} (got {n})")
    if strict_r < STEP2_MIN_STRICT_FORMAT_RATE:
        failures.append(
            f"strict_format_rate>={STEP2_MIN_STRICT_FORMAT_RATE} (got {strict_r:.4f})"
        )
    if acc < STEP2_MIN_ACCURACY:
        failures.append(f"accuracy>={STEP2_MIN_ACCURACY} (got {acc:.4f})")
    if null_r > STEP2_MAX_PREDICTED_NULL_RATE:
        failures.append(
            f"predicted_null_rate<={STEP2_MAX_PREDICTED_NULL_RATE} (got {null_r:.4f})"
        )
    if api_r > STEP2_MAX_API_ERROR_RATE:
        failures.append(
            f"api_error_rate<={STEP2_MAX_API_ERROR_RATE} "
            f"(got {api_r:.4f}, api_error={api_n}, verify_api_error={vfy_n})"
        )

    passed = len(failures) == 0
    detail: Dict[str, Any] = {
        "passed": passed,
        "reference": "docs/vertex/STEP2_QUALITY_GATES.md",
        "thresholds": {
            "min_n_problems": STEP2_MIN_PROBLEMS,
            "min_strict_format_rate": STEP2_MIN_STRICT_FORMAT_RATE,
            "min_accuracy": STEP2_MIN_ACCURACY,
            "max_predicted_null_rate": STEP2_MAX_PREDICTED_NULL_RATE,
            "max_api_error_rate": STEP2_MAX_API_ERROR_RATE,
        },
        "observed": {
            "n_problems": n,
            "strict_format_rate": strict_r,
            "accuracy": acc,
            "predicted_null_rate": null_r,
            "api_error_count": api_n,
            "verify_api_error_count": vfy_n,
            "api_error_total_count": api_total,
            "api_error_rate": api_r,
        },
        "failures": failures,
    }
    return passed, detail


def _eval_accuracy_breakdowns(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    JSONL 행 기준: 채점 경로별·strict 형식 여부별 정확도.
    원인 분석(폴백 vs 검수 vs strict)과 단계별 목표 추적에 사용.
    """
    by_status: Dict[str, Dict[str, Any]] = {}
    by_strict = {"true": {"n": 0, "correct": 0}, "false": {"n": 0, "correct": 0}}
    for r in rows:
        ss = str(r.get("scoring_status") or "unknown")
        if ss not in by_status:
            by_status[ss] = {"n": 0, "correct": 0}
        by_status[ss]["n"] += 1
        if r.get("is_correct") is True:
            by_status[ss]["correct"] += 1
        if r.get("strict_format_ok") is True:
            by_strict["true"]["n"] += 1
            if r.get("is_correct") is True:
                by_strict["true"]["correct"] += 1
        else:
            by_strict["false"]["n"] += 1
            if r.get("is_correct") is True:
                by_strict["false"]["correct"] += 1
    for d in by_status.values():
        n = int(d["n"])
        d["accuracy"] = (float(d["correct"]) / n) if n else 0.0
    for key in ("true", "false"):
        d = by_strict[key]
        n = int(d["n"])
        d["accuracy"] = (float(d["correct"]) / n) if n else 0.0
    return {
        "accuracy_by_scoring_status": by_status,
        "accuracy_by_strict_format_ok": by_strict,
    }


def _sanitize_for_json(obj: Any) -> Any:
    """JSON 직렬화 불가 값(Ellipsis, numpy 등) 제거."""
    if obj is Ellipsis:
        return None
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(x) for x in obj]
    if hasattr(obj, "item") and callable(getattr(obj, "item", None)):
        try:
            return _sanitize_for_json(obj.item())
        except Exception:
            return str(obj)
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description="Vertex 엔드포인트 답 품질 샘플 평가")
    ap.add_argument(
        "--endpoint-id",
        required=True,
        help="Vertex Endpoint ID (숫자) 또는 projects/.../endpoints/... 전체 이름",
    )
    ap.add_argument("--project", default=resolve_project_id(prefer_cleanup_alias=False))
    ap.add_argument("--location", default=resolve_location())
    ap.add_argument("--n-problems", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--data-file", default=NUMINA_TRAINING_FILE, help="evaluation.config find_data_file 기준 파일명")
    ap.add_argument(
        "--sources",
        default="",
        help=(
            "쉼표 구분 소스 허용 목록(소문자 무시). 예: orca_math,cn_k12. "
            "비우면 전체. `numinamath_full.jsonl` 에서 orca_math·cn_k12 등 혼합 소스 사용."
        ),
    )
    ap.add_argument(
        "--difficulty-at-most",
        choices=("easy", "medium", "hard"),
        default=None,
        help=(
            "소스 기준 난이도 상한(evaluation_utils.determine_difficulty_from_source). "
            "easy=orca/gsm8k만, medium=hard 소스 제외, hard=필터 없음."
        ),
    )
    ap.add_argument(
        "--max-new-tokens",
        type=int,
        default=_default_max_new_tokens(),
        help="생성 토큰 상한(서빙으로 전달). 0이면 서버가 컨텍스트에 맞게 채움. env: VERTEX_MAX_NEW_TOKENS (기본 8192)",
    )
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument(
        "--predict-timeout",
        type=float,
        default=float(os.getenv("VERTEX_PREDICT_TIMEOUT_SECONDS", "600")),
        help=(
            "SDK predict 타임아웃(초). None/0/짧은 값은 gRPC ~60초 한도로 503이 난다. "
            "기본 600; 상한 VERTEX_PREDICT_TIMEOUT_MAX(기본 600), 최소 VERTEX_PREDICT_TIMEOUT_MIN(기본 90). "
            "env: VERTEX_PREDICT_TIMEOUT_SECONDS"
        ),
    )
    ap.add_argument(
        "--vertex-predict-retries",
        type=int,
        default=int(os.getenv("VERTEX_PREDICT_TRANSIENT_RETRIES", "3")),
        help=(
            "503/지연 등 일시 오류 시 predict 재시도 횟수(형식 시도·검수 호출마다). "
            "env: VERTEX_PREDICT_TRANSIENT_RETRIES"
        ),
    )
    ap.add_argument(
        "--vertex-predict-retry-delay",
        type=float,
        default=float(os.getenv("VERTEX_PREDICT_RETRY_DELAY", "5")),
        help="재시도 전 대기(초), 선형 증가(1x,2x,...). env: VERTEX_PREDICT_RETRY_DELAY",
    )
    ap.add_argument(
        "--output",
        default="",
        help="JSONL 결과 경로 (미지정 시 results/vertex_eval_<ts>.jsonl)",
    )
    ap.add_argument(
        "--max-format-retries",
        type=int,
        default=int(os.getenv("VERTEX_MAX_FORMAT_RETRIES", "3")),
        help="<ANS> strict 불통과 시 추가 생성 횟수. 0이면 1회만. env: VERTEX_MAX_FORMAT_RETRIES",
    )
    ap.add_argument(
        "--retry-temperature",
        type=float,
        default=float(os.getenv("VERTEX_RETRY_TEMPERATURE", "0.35")),
        help="재시도 시 샘플링 온도(첫 시도는 --temperature).",
    )
    ap.add_argument(
        "--no-format-gate",
        action="store_true",
        help="형식 게이트·재시도 없이 구 프롬프트 1회만 (비교용).",
    )
    ap.add_argument(
        "--no-fallback-boxed",
        action="store_true",
        help="형식 실패 시 \\boxed{} / 추출기 완화 채점 안 함.",
    )
    ap.add_argument(
        "--last-resort-extraction",
        action="store_true",
        help=(
            "박스·ANS 실패 후 tail 휴리스틱(영문 answer is / 마지막 숫자 줄 등). "
            "기본 off. env AIMO_EVAL_LAST_RESORT_EXTRACTION=1"
        ),
    )
    ap.add_argument(
        "--no-verify-agent",
        action="store_true",
        help="답이 비었을 때 검수(정리) 2차 Vertex 호출 안 함. env VERTEX_VERIFY_AGENT=0 과 동일 효과.",
    )
    ap.add_argument(
        "--verify-max-new-tokens",
        type=int,
        default=int(os.getenv("VERTEX_VERIFY_MAX_NEW_TOKENS", "1024")),
        help="검수 Agent 생성 토큰 상한. env: VERTEX_VERIFY_MAX_NEW_TOKENS",
    )
    ap.add_argument(
        "--verify-temperature",
        type=float,
        default=float(os.getenv("VERTEX_VERIFY_TEMPERATURE", "0.0")),
        help="검수 Agent 샘플링 온도. env: VERTEX_VERIFY_TEMPERATURE",
    )
    ap.add_argument(
        "--bq-table",
        default=os.getenv("VERTEX_EVAL_BQ_TABLE", "").strip(),
        help="BigQuery 적재: project.dataset.table (미지정 시 JSONL만 저장). env: VERTEX_EVAL_BQ_TABLE",
    )
    ap.add_argument(
        "--bq-no-create",
        action="store_true",
        help="BigQuery 데이터셋/테이블 자동 생성 안 함",
    )
    ap.add_argument(
        "--bq-dataset-location",
        default=os.getenv("VERTEX_EVAL_BQ_DATASET_LOCATION", "asia-northeast3"),
        help="데이터셋이 없을 때 생성 리전",
    )
    ap.add_argument(
        "--enforce-gates",
        action="store_true",
        help=(
            "STEP2_QUALITY_GATES.md 임계값과 비교해 미충족 시 exit code 2. "
            "문서·상수(STEP2_*)와 맞출 것."
        ),
    )
    ap.add_argument(
        "--write-summary-json",
        default="",
        help="요약 dict를 JSON 파일로 저장 (Ralph 게이트·CI). Vertex summary의 accuracy는 [0,1] 비율.",
    )
    ap.add_argument(
        "--enforce-ralph-accuracy",
        action="store_true",
        help=(
            "평가 후 Ralph 목표 정확도 미달이면 exit 1. "
            "기준: AIMO_RALPH_TARGET_ACCURACY_PCT (기본 80). "
            "eval_vertex_endpoint_quality 의 accuracy 비율(0~1)과 호환."
        ),
    )
    args = ap.parse_args()

    use_verify_agent = (not args.no_verify_agent) and _env_bool("VERTEX_VERIFY_AGENT", True)
    last_resort = bool(args.last_resort_extraction) or _env_bool("AIMO_EVAL_LAST_RESORT_EXTRACTION", False)

    try:
        from google.cloud import aiplatform
    except ImportError as e:
        print("ERROR: google-cloud-aiplatform 필요:", e, file=sys.stderr)
        return 1

    out_path = args.output
    if not out_path:
        ts = time.strftime("%Y%m%d_%H%M%S")
        ensure_dir(RESULTS_DIR)
        out_path = str(RESULTS_DIR / f"vertex_eval_{ts}.jsonl")

    allow = _parse_sources_csv(args.sources)
    problems = load_numina_jsonl_filtered(
        args.n_problems,
        args.seed,
        filename=args.data_file,
        sources_allowlist=allow if allow else None,
        difficulty_at_most=args.difficulty_at_most,
    )
    aiplatform.init(project=args.project, location=args.location)

    endpoint = aiplatform.Endpoint(args.endpoint_id)
    extractor = AnswerExtractor()

    rows: List[Dict[str, Any]] = []
    correct = 0
    strict_ok = 0
    fallback_graded = 0
    verify_agent_calls = 0
    verify_agent_recovered = 0
    nonempty_raw_predicted_null = 0
    scoring_status_counts: Dict[str, int] = {}
    extraction_route_counts: Dict[str, int] = {}
    match_breakdown: Dict[str, int] = {
        "strict": 0,
        "sympy": 0,
        "numeric": 0,
        "ratio": 0,
        "interval": 0,
        "none": 0,
    }

    iterator: Any = enumerate(problems)
    try:
        from tqdm import tqdm

        iterator = tqdm(iterator, total=len(problems), desc="vertex_eval")
    except Exception:
        pass

    fallback_boxed = not args.no_fallback_boxed
    predict_timeout_eff = _effective_predict_timeout(float(args.predict_timeout))

    with open(out_path, "w", encoding="utf-8") as out_f:
        for j, p in iterator:
            if args.no_format_gate:
                prompt = build_prompt_legacy(p.problem)
                t0 = time.time()
                resp, pred_err, ltrace = _endpoint_predict_with_retries(
                    endpoint,
                    [
                        {
                            "prompt": prompt,
                            "max_new_tokens": args.max_new_tokens,
                            "temperature": args.temperature,
                        }
                    ],
                    predict_timeout_eff,
                    transient_retries=int(args.vertex_predict_retries),
                    retry_delay_s=float(args.vertex_predict_retry_delay),
                )
                dt = time.time() - t0
                if pred_err is not None:
                    text = ""
                    ext_err = pred_err
                else:
                    preds = getattr(resp, "predictions", None) or []
                    raw = preds[0] if preds else None
                    text = _prediction_text(raw)
                    ext_err = None

                fmt_ok = bool(validate_ans_strict(text or "").ok) if ext_err is None else False
                lprog: Optional[Dict[str, Any]] = None
                if ext_err is not None:
                    lprog = {
                        "failed_at": "legacy_single_shot",
                        "outcome": "api_error",
                        "transient_retries_configured": int(args.vertex_predict_retries),
                        "predict_timeout_s": predict_timeout_eff,
                        "predict_calls": [{**c, "stage": "legacy"} for c in ltrace],
                    }
                gen = {
                    "text": text,
                    "format_ok": fmt_ok,
                    "format_reason": None if fmt_ok else "legacy_single_shot",
                    "attempts": 1,
                    "error": ext_err,
                    "latency_s": round(dt, 3),
                    "predict_progress": lprog,
                }
            else:
                gen = vertex_predict_with_format_retries(
                    endpoint,
                    p.problem,
                    max_new_tokens=args.max_new_tokens,
                    base_temperature=args.temperature,
                    retry_temperature=args.retry_temperature,
                    max_format_retries=args.max_format_retries,
                    predict_timeout=predict_timeout_eff,
                    transient_retries=int(args.vertex_predict_retries),
                    retry_delay_s=float(args.vertex_predict_retry_delay),
                )
                text = gen.get("text") or ""
                dt = float(gen.get("latency_s", 0))
                ext_err = gen.get("error")

            fmt_ok = bool(gen.get("format_ok")) and ext_err is None
            if fmt_ok:
                strict_ok += 1

            pred_str, ok, scoring_status, ext_d = grade_completion_for_eval(
                p.answer,
                text,
                format_ok=fmt_ok,
                fallback_boxed=fallback_boxed,
                last_resort=last_resort,
                extractor=extractor,
            )
            if scoring_status == "graded_fallback":
                fallback_graded += 1
            if ext_err is not None:
                scoring_status = "api_error"
                ok = False

            dt_total = float(dt)
            verify_block: Optional[Dict[str, Any]] = None
            if (
                use_verify_agent
                and ext_err is None
                and pred_str is None
            ):
                verify_agent_calls += 1
                verify_block = _run_verification_agent(
                    endpoint,
                    problem_text=p.problem,
                    raw_text=text,
                    max_new_tokens=max(64, int(args.verify_max_new_tokens)),
                    temperature=float(args.verify_temperature),
                    predict_timeout=predict_timeout_eff,
                    transient_retries=int(args.vertex_predict_retries),
                    retry_delay_s=float(args.vertex_predict_retry_delay),
                )
                dt_total += float(verify_block.get("latency_s", 0))
                if verify_block.get("error") is None:
                    vt = verify_block.get("text") or ""
                    v_fmt_ok = bool(verify_block.get("format_ok"))
                    pred_v, ok_v, status_v, ext_v = grade_completion_for_eval(
                        p.answer,
                        vt,
                        format_ok=v_fmt_ok,
                        fallback_boxed=fallback_boxed,
                        last_resort=last_resort,
                        extractor=extractor,
                    )
                    if pred_v is not None:
                        verify_agent_recovered += 1
                        pred_str, ok, ext_d = pred_v, ok_v, ext_v
                        if status_v == "graded":
                            scoring_status = "graded_verify_agent"
                        elif status_v == "graded_fallback":
                            scoring_status = "graded_fallback_verify_agent"
                            fallback_graded += 1
                        else:
                            scoring_status = f"{status_v}_verify_agent"
                else:
                    scoring_status = "verify_api_error"
                    ok = False

            if ok:
                correct += 1

            mk = classify_answer_match(p.answer, pred_str) if pred_str else "none"
            match_breakdown[mk] = match_breakdown.get(mk, 0) + 1

            scoring_status_counts[scoring_status] = scoring_status_counts.get(scoring_status, 0) + 1
            route = ext_d.get("extraction_route") if isinstance(ext_d, dict) else None
            if route:
                extraction_route_counts[route] = extraction_route_counts.get(route, 0) + 1
            if (
                pred_str is None
                and (text or "").strip()
                and ext_err is None
            ):
                nonempty_raw_predicted_null += 1

            vrow = (
                _sanitize_for_json(_verify_agent_row(verify_block)) if verify_block else None
            )
            pp_top: Optional[Dict[str, Any]] = gen.get("predict_progress")
            if verify_block and verify_block.get("error"):
                pp_top = verify_block.get("predict_progress") or pp_top
            row_error: Optional[str] = ext_err
            if row_error is None and verify_block:
                row_error = verify_block.get("error")
            row = {
                "sample_idx": j,
                "problem_id": p.idx,
                "source": p.source,
                "difficulty": determine_difficulty_from_source(p.source),
                "reference_answer": p.answer,
                "latency_s": round(dt_total, 3),
                "error": row_error,
                "strict_format_ok": fmt_ok,
                "format_attempts": gen.get("attempts"),
                "format_failure_reason": (None if fmt_ok else gen.get("format_reason")),
                "scoring_status": scoring_status,
                "extraction_route": route,
                "raw_text_head": (text[:800] if text else ""),
                "extracted": ext_d,
                "predicted_answer": pred_str,
                "is_correct": ok,
                "match_kind": mk,
                "predict_progress": _sanitize_for_json(pp_top),
                "verify_agent": vrow,
            }
            row = _sanitize_for_json(row)
            rows.append(row)
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")

    n = len(rows)
    acc = correct / n if n else 0.0
    predicted_null = sum(1 for r in rows if r.get("predicted_answer") is None)
    breakdowns = _eval_accuracy_breakdowns(rows)
    verify_recovery_rate = (
        (verify_agent_recovered / verify_agent_calls) if verify_agent_calls else None
    )
    summary: Dict[str, Any] = {
        "endpoint_id": args.endpoint_id,
        "project": args.project,
        "location": args.location,
        "n_problems": n,
        "correct": correct,
        "accuracy": acc,
        "match_kind_breakdown": match_breakdown,
        "scoring_status_breakdown": scoring_status_counts,
        "extraction_route_breakdown": extraction_route_counts,
        "predicted_null_count": predicted_null,
        "predicted_null_rate": (predicted_null / n if n else 0.0),
        "nonempty_raw_predicted_null_count": nonempty_raw_predicted_null,
        "nonempty_raw_predicted_null_rate": (
            nonempty_raw_predicted_null / n if n else 0.0
        ),
        "strict_format_ok": strict_ok,
        "strict_format_rate": (strict_ok / n if n else 0.0),
        "graded_fallback_rows": fallback_graded,
        "last_resort_extraction": last_resort,
        "verify_agent_enabled": use_verify_agent,
        "verify_agent_calls": verify_agent_calls,
        "verify_agent_recovered": verify_agent_recovered,
        "verify_agent_recovery_rate": verify_recovery_rate,
        **breakdowns,
        "max_format_retries": args.max_format_retries,
        "format_gate": not args.no_format_gate,
        "fallback_boxed": fallback_boxed,
        "predict_timeout_requested": float(args.predict_timeout),
        "predict_timeout_effective": predict_timeout_eff,
        "predict_timeout_max_seconds": _predict_timeout_max_cap(),
        "seed": args.seed,
        "data_file": args.data_file,
        "output": out_path,
    }

    gate_passed = True
    if args.enforce_gates:
        gate_passed, gate_detail = _step2_gate_check(summary)
        summary["step2_gate"] = gate_detail

    if args.bq_table:
        try:
            from vertex_bigquery import new_run_id, upload_jsonl_to_bigquery
        except ImportError as e:
            print("ERROR: BigQuery 적재에 google-cloud-bigquery 필요:", e, file=sys.stderr)
            print("  pip install -r requirements-vertex-bq.txt", file=sys.stderr)
            return 1
        try:
            bq_run = new_run_id()
            bq_n, bq_rid = upload_jsonl_to_bigquery(
                Path(out_path),
                table=args.bq_table,
                run_id=bq_run,
                endpoint_id=str(args.endpoint_id),
                vertex_project=args.project,
                vertex_location=args.location,
                create_table=not args.bq_no_create,
                dataset_location=args.bq_dataset_location,
            )
            summary["bigquery"] = {
                "table": args.bq_table,
                "run_id": bq_rid,
                "uploaded_rows": bq_n,
            }
        except Exception as e:
            print("ERROR: BigQuery 적재 실패:", e, file=sys.stderr)
            return 1

    wsj = (args.write_summary_json or "").strip()
    if wsj:
        wsj_path = Path(wsj)
        wsj_path.parent.mkdir(parents=True, exist_ok=True)
        with wsj_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"Wrote summary JSON: {wsj_path}", flush=True)

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.enforce_gates and not gate_passed:
        fails = summary.get("step2_gate", {}).get("failures") or []
        print("STEP2 gate FAIL:", "; ".join(fails), file=sys.stderr)
        return 2

    if args.enforce_ralph_accuracy:
        from evaluation.ralph_accuracy import evaluate_vertex_summary_for_ralph

        ok_r, msg_r, _, _ = evaluate_vertex_summary_for_ralph(summary)
        print(msg_r, flush=True)
        if not ok_r:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
