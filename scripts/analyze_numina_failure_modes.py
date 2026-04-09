#!/usr/bin/env python3
"""
Numina (save_results JSON) 오답을 범주로 나눈다.

- JSON에 `eval_failure_axis` 가 있으면(새 평가 실행) 그대로 사용한다.
- 없으면 예전 휴리스틱만 사용한다(`extraction_recoverable` 은 나오지 않을 수 있음).

1) pipeline_or_empty — 예측 없음/실패 메서드
2) extraction_recoverable — 채점은 틀렸지만, 원문에서 다른 추출 후보가 정답과 일치
3) format_or_grading — 표기·밑 진법·느슨한 수치 등
4) reasoning_or_extraction — 그 외 (추론·독해 오류 가능성)

사용:
  python scripts/analyze_numina_failure_modes.py results/foo.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
_SRC = ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from evaluation.evaluation_utils import (  # noqa: E402
    classify_answer_match,
    normalize_answer,
    numeric_equivalent,
)

FAILURE_METHODS = frozenset(
    {
        "all_failed_rate_limited",
        "all_failed",
        "timeout",
        "worker_exception",
    }
)


def _pred_empty(pred: Any) -> bool:
    if pred is None:
        return True
    s = str(pred).strip()
    return s == "" or s.upper() == "N/A"


def _base_notation_missing_subscript(ref: str, pred: Any) -> bool:
    """정답이 '1000_7' 형태이고 예측이 밑만 빠진 '1000'인 경우."""
    if not ref or pred is None:
        return False
    ref_s = str(ref).strip()
    pred_s = str(pred).strip()
    m = re.match(r"^(.+)_(\d+)$", ref_s)
    if not m:
        return False
    core = m.group(1).strip()
    return normalize_answer(core) == normalize_answer(pred_s)


def _loose_numeric_would_pass(ref: str, pred: Any) -> bool:
    """기본 채점은 실패했지만 수치만 보면 거의 같은 경우 (반올림·표기 차)."""
    if not ref or pred is None:
        return False
    if classify_answer_match(ref, pred, use_sympy=True) != "none":
        return False
    rn = normalize_answer(str(ref))
    pn = normalize_answer(str(pred))
    if not rn or not pn:
        return False
    return numeric_equivalent(rn, pn, rtol=0.05, atol=1e-5)


def categorize_row(row: Dict[str, Any]) -> str:
    axis = row.get("eval_failure_axis")
    if isinstance(axis, str) and axis.strip():
        a = axis.strip()
        if a == "correct":
            return "correct"
        if a == "pipeline_or_empty":
            return "pipeline_or_empty"
        if a == "extraction_recoverable":
            return "extraction_recoverable"
        if a == "format_or_grading":
            return "format_or_grading"
        if a == "reasoning_likely":
            return "reasoning_or_extraction"

    if row.get("is_correct"):
        return "correct"

    pred = row.get("predicted_answer")
    method = str(row.get("method") or "")

    if _pred_empty(pred) or method in FAILURE_METHODS:
        return "pipeline_or_empty"

    ref = row.get("reference_answer") or ""

    if _base_notation_missing_subscript(ref, pred):
        return "format_or_grading"

    if _loose_numeric_would_pass(ref, pred):
        return "format_or_grading"

    return "reasoning_or_extraction"


def main() -> int:
    ap = argparse.ArgumentParser(description="Classify Numina result rows into failure modes.")
    ap.add_argument("json_path", type=Path, help="save_results() 형식 JSON")
    ap.add_argument("--incorrect-only", action="store_true", help="오답 행만 표로 출력")
    args = ap.parse_args()
    path = args.json_path
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    rows: List[Dict[str, Any]] = data.get("results") or []
    if not rows:
        print("No results[] in JSON", file=sys.stderr)
        return 1

    counts = Counter(categorize_row(r) for r in rows)
    n = len(rows)
    print(f"File: {path}")
    print(f"Total rows: {n}")
    print()
    order = (
        "correct",
        "pipeline_or_empty",
        "extraction_recoverable",
        "format_or_grading",
        "reasoning_or_extraction",
    )
    for k in order:
        c = counts.get(k, 0)
        print(f"  {k:26s}  {c:3d}  ({100.0 * c / n:5.1f}%)")

    if any("counterfactual_would_pass" in r for r in rows):
        cf = sum(1 for r in rows if r.get("counterfactual_would_pass"))
        print()
        print(
            f"  counterfactual_would_pass   {cf:3d}  ({100.0 * cf / n:5.1f}%)  "
            "(맞았거나 alternate 추출이 정답과 일치)"
        )

    if args.incorrect_only:
        print("\n--- incorrect rows (id, bucket, method, ref, pred) ---")
        for r in rows:
            if r.get("is_correct"):
                continue
            b = categorize_row(r)
            pid = r.get("problem_id")
            ref = (r.get("reference_answer") or "")[:50]
            pred = r.get("predicted_answer")
            print(f"  {pid:2}  {b:22}  {r.get('method')}  ref={ref!r} pred={pred!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
