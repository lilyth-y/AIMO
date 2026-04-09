#!/usr/bin/env python3
"""
Export AIMO evaluation JSON (EvaluationMetrics.save_results format) to static files
consumed by dashboard/src/pages/Process.tsx:

  - dashboard/public/numina_eval_balanced.json  — array of Problem-shaped rows
  - dashboard/public/eval_data.json             — array of EvalData-shaped rows

Usage:
  python scripts/export_dashboard_process.py results/numinamath_full_results_max_easy.json

Notes:
  - Saved results often truncate ``problem`` to 200 chars (see EvaluationResult.to_dict).
    For full problem text in the dashboard, extend evaluation export or merge from
    another source before running this script.
  - True model CoT is not stored in standard save_results; ``solution`` / reasoning
    steps are synthesized from reference/predicted/method/error for display.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _problem_row(r: Dict[str, Any]) -> Dict[str, Any]:
    ref = r.get("reference_answer")
    pred = r.get("predicted_answer")
    method = r.get("method") or "unknown"
    err = r.get("error")
    ok = r.get("is_correct")
    lines = [
        "**평가 요약** (표준 `save_results`에서 합성)",
        "",
        f"- **정답 여부:** `{'✓' if ok else '✗'}`",
        f"- **방법:** `{method}`",
    ]
    if err:
        lines.append(f"- **에러:** `{err}`")
    lines.extend(
        [
            "",
            "**정답 (레퍼런스):**",
            f"`{ref}`",
            "",
            "**모델 예측:**",
            f"`{pred}`",
            "",
            "*원본 Chain-of-Thought 전문은 이 JSON에 포함되지 않습니다. 파이프라인 로그나 별도 추출이 필요합니다.*",
        ]
    )
    solution = "\n".join(lines)
    return {
        "problem": r.get("problem") or "",
        "solution": solution,
        "answer": str(ref) if ref is not None else "",
        "source": str(r.get("source") or "unknown"),
        "problem_type": str(r.get("problem_type") or "Other"),
        "question_type": str(r.get("question_type") or "math-word-problem"),
        "problem_id": r.get("problem_id"),
        "is_correct": ok,
        "method": method,
        "predicted_answer": pred,
        "reference_answer": ref,
    }


def _eval_row(r: Dict[str, Any]) -> Dict[str, Any]:
    method = str(r.get("method") or "AIMO")
    err = r.get("error")
    pred = r.get("predicted_answer")
    ref = r.get("reference_answer")
    body = "\n".join(
        [
            f"**Method:** `{method}`",
            f"**Correct:** `{r.get('is_correct')}`",
            "",
            f"**Reference:** `{ref}`",
            f"**Predicted:** `{pred}`",
        ]
    )
    reasoning_steps = [
        {
            "step": "evaluation_record",
            "params": {
                "iteration": 1,
                "llm_response": body,
            },
        }
    ]
    out: Dict[str, Any] = {
        "query": r.get("problem") or "",
        "response": str(pred) if pred is not None else "",
        "reasoning_steps": reasoning_steps,
        "result": {
            "output": str(pred) if pred is not None else None,
            "error": str(err) if err else None,
            "traceback": None,
        },
        "tools": [],
        "type": method,
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "eval_json",
        type=Path,
        help="Path to save_results JSON (e.g. results/foo.json)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: dashboard/public)",
    )
    args = ap.parse_args()
    root = _repo_root()
    out_dir = args.out_dir or (root / "dashboard" / "public")
    out_dir.mkdir(parents=True, exist_ok=True)

    path = args.eval_json
    if not path.is_absolute():
        path = (root / path).resolve()
    if not path.is_file():
        print(f"Not found: {path}", file=sys.stderr)
        return 1

    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    results: List[Dict[str, Any]] = data.get("results") or []
    if not results:
        print("No 'results' array in JSON.", file=sys.stderr)
        return 1

    problems_out: List[Dict[str, Any]] = [_problem_row(r) for r in results]
    eval_out: List[Dict[str, Any]] = [_eval_row(r) for r in results]

    p1 = out_dir / "numina_eval_balanced.json"
    p2 = out_dir / "eval_data.json"
    with p1.open("w", encoding="utf-8") as f:
        json.dump(problems_out, f, ensure_ascii=False, indent=2)
    with p2.open("w", encoding="utf-8") as f:
        json.dump(eval_out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(problems_out)} rows -> {p1}")
    print(f"Wrote {len(eval_out)} rows -> {p2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
