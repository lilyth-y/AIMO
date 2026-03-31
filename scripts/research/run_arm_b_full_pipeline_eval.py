"""
연구 프로토콜 Arm B — Full-Pipeline (`PipelineOrchestrator.solve_problem`).

- 문제 풀·정답: `eval_hf_local_quality.py` 와 동일 (`load_numina_jsonl_filtered`, 동일 seed/data_file/n)
- 채점: `check_answer_correctness(reference, predicted_str)`
- 형식: `solver.last_reasoning` 이 있으면 `validate_ans_strict` 로 `strict_format_ok` (Arm A와 최대한 동일 축)

주의: LLM·실행 환경이 필요하고 문제당 시간이 길 수 있음. `--n-problems` 는 작게 시작.

사용:
  python scripts/research/run_arm_b_full_pipeline_eval.py --n-problems 5 --seed 41 --time-budget 120
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from evaluation.config import NUMINA_TRAINING_FILE, ensure_dir  # noqa: E402
from evaluation.evaluation_utils import (  # noqa: E402
    check_answer_correctness,
    determine_difficulty_from_source,
)
from pipeline.ans_format_guard import validate_ans_strict  # noqa: E402


def _load_eval_loader():
    """eval_hf_local_quality 의 문제 풀 로더만 재사용 (동일 샘플 재현)."""
    path = _ROOT / "scripts" / "eval_hf_local_quality.py"
    spec = importlib.util.spec_from_file_location("eval_hf_local_quality", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_numina_jsonl_filtered


def _json_safe(obj: Any) -> Any:
    if obj is Ellipsis:
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    return str(obj)


def main() -> int:
    ap = argparse.ArgumentParser(description="Arm B: Full-Pipeline 배치 평가")
    ap.add_argument("--n-problems", type=int, default=10)
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--data-file", default=NUMINA_TRAINING_FILE)
    ap.add_argument("--time-budget", type=float, default=120.0, help="solve_problem 시간 상한(초)")
    ap.add_argument("--domain", default="general_math")
    ap.add_argument(
        "--output",
        default="",
        help="JSONL (기본: results/research/arm_b_full_<seed>_<n>p.jsonl)",
    )
    args = ap.parse_args()

    load_numina_jsonl_filtered = _load_eval_loader()
    problems = load_numina_jsonl_filtered(args.n_problems, args.seed, filename=args.data_file)

    out_path = args.output
    if not out_path:
        ensure_dir(_ROOT / "results" / "research")
        out_path = str(_ROOT / "results" / "research" / f"arm_b_full_{args.seed}_{args.n_problems}p.jsonl")

    from pipeline.orchestrator import PipelineOrchestrator

    orch = PipelineOrchestrator()

    correct = 0
    strict_ok = 0
    rows: List[Dict[str, Any]] = []

    try:
        from tqdm import tqdm
    except Exception:
        tqdm = None

    it = tqdm(enumerate(problems), total=len(problems), desc="arm_b_full") if tqdm else enumerate(problems)

    with open(out_path, "w", encoding="utf-8") as out_f:
        for j, p in it:
            t0 = time.time()
            err = None
            try:
                res = orch.solve_problem(
                    domain=args.domain,
                    variables={},
                    problem_text=p.problem,
                    time_budget=args.time_budget,
                )
            except Exception as e:
                err = str(e)
                res = {}
            dt = time.time() - t0

            pred = None
            if res and not err:
                pred = res.get("extracted_answer")
                if pred is None:
                    pred = res.get("answer")

            pred_str = None
            if pred is not None and pred is not Ellipsis:
                pred_str = str(pred)

            ok = bool(check_answer_correctness(p.answer, pred_str)) if err is None else False
            if ok:
                correct += 1

            reasoning = getattr(orch.solver, "last_reasoning", None) or ""
            fmt = validate_ans_strict(reasoning or "")
            fmt_ok = bool(fmt.ok)
            if fmt_ok:
                strict_ok += 1

            row = {
                "arm": "B_full_pipeline",
                "sample_idx": j,
                "problem_id": p.idx,
                "source": p.source,
                "difficulty": determine_difficulty_from_source(p.source),
                "reference_answer": p.answer,
                "latency_s": round(dt, 3),
                "error": err,
                "method": (res or {}).get("method"),
                "verified": (res or {}).get("verified"),
                "strict_format_ok": fmt_ok,
                "format_failure_reason": fmt.reason,
                "predicted_answer": pred_str,
                "is_correct": ok,
            }
            rows.append(row)
            out_f.write(json.dumps(_json_safe(row), ensure_ascii=False) + "\n")

    n = len(rows)
    summary = {
        "arm": "B_full_pipeline",
        "n_problems": n,
        "correct": correct,
        "accuracy": correct / n if n else 0.0,
        "strict_format_compliance": {
            "passed": strict_ok,
            "rate": strict_ok / n if n else 0.0,
        },
        "seed": args.seed,
        "data_file": args.data_file,
        "time_budget": args.time_budget,
        "domain": args.domain,
        "output": out_path,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
