"""
Arm A vs Arm B JSONL 비교 (동일 problem_id 기준).

입력: `eval_hf_local_quality.py` / `eval_vertex_endpoint_quality.py` / 동일 스키마의 JSONL 두 개.
  - 필수: 각 줄에 `problem_id`, `is_correct`
  - 선택: `strict_format_ok` (HF 로컬 평가에 있음). Vertex 단독 JSONL은 strict 집계를 생략할 수 있음.

사용:
  python scripts/research/compare_research_arms.py \\
    --a results/research/arm_a_baseline_41_100p.jsonl \\
    --b results/some_arm_b.jsonl \\
    --label-a ArmA_Baseline --label-b ArmB_Pipeline

출력: stdout JSON (paired 수, 정확도, strict 차이, McNemar 스타일 분할 표).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_by_problem_id(path: Path) -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = obj.get("problem_id")
            if pid is None:
                continue
            out[int(pid)] = obj
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="연구 Arm A/B JSONL 비교")
    ap.add_argument("--a", required=True, type=Path, help="Arm A JSONL")
    ap.add_argument("--b", required=True, type=Path, help="Arm B JSONL")
    ap.add_argument("--label-a", default="arm_a")
    ap.add_argument("--label-b", default="arm_b")
    ap.add_argument("--output-json", type=Path, default=None, help="요약 JSON 저장 경로")
    args = ap.parse_args()

    if not args.a.is_file():
        print(f"ERROR: --a not found: {args.a}", file=sys.stderr)
        return 1
    if not args.b.is_file():
        print(f"ERROR: --b not found: {args.b}", file=sys.stderr)
        return 1

    da = load_by_problem_id(args.a)
    db = load_by_problem_id(args.b)
    ids = sorted(set(da.keys()) & set(db.keys()))

    if not ids:
        print("ERROR: problem_id 교집합이 비어 있습니다. seed·data_file·n_problems가 동일한지 확인하세요.", file=sys.stderr)
        return 1

    # Paired stats
    correct_a = correct_b = 0
    strict_a = strict_b = 0
    strict_pairs = 0
    # McNemar table: (a wrong, b wrong), (a right, b wrong), ...
    # b_correct x a_correct
    both_wrong = a_only_right = b_only_right = both_right = 0

    for pid in ids:
        ra, rb = da[pid], db[pid]
        ca = bool(ra.get("is_correct"))
        cb = bool(rb.get("is_correct"))
        if ca:
            correct_a += 1
        if cb:
            correct_b += 1
        if ca and cb:
            both_right += 1
        elif ca and not cb:
            a_only_right += 1
        elif not ca and cb:
            b_only_right += 1
        else:
            both_wrong += 1

        sa = ra.get("strict_format_ok")
        sb = rb.get("strict_format_ok")
        if sa is not None and sb is not None:
            strict_pairs += 1
            if sa:
                strict_a += 1
            if sb:
                strict_b += 1

    n = len(ids)
    acc_a = correct_a / n
    acc_b = correct_b / n
    delta_acc = acc_b - acc_a

    summary: Dict[str, Any] = {
        "labels": {"a": args.label_a, "b": args.label_b},
        "files": {"a": str(args.a.resolve()), "b": str(args.b.resolve())},
        "n_paired": n,
        "n_only_a": len(set(da.keys()) - set(db.keys())),
        "n_only_b": len(set(db.keys()) - set(da.keys())),
        "accuracy": {
            "arm_a": {"label": args.label_a, "rate": round(acc_a, 6)},
            "arm_b": {"label": args.label_b, "rate": round(acc_b, 6)},
            "delta_b_minus_a": round(delta_acc, 6),
        },
        "paired_contingency_is_correct": {
            "both_wrong": both_wrong,
            "a_only_right": a_only_right,
            "b_only_right": b_only_right,
            "both_right": both_right,
        },
        "strict_format": None,
    }

    if strict_pairs > 0:
        sr_a = strict_a / strict_pairs
        sr_b = strict_b / strict_pairs
        summary["strict_format"] = {
            "n_both_have_field": strict_pairs,
            "arm_a": {"label": args.label_a, "rate": round(sr_a, 6)},
            "arm_b": {"label": args.label_b, "rate": round(sr_b, 6)},
            "delta_b_minus_a": round(sr_b - sr_a, 6),
        }
    else:
        summary["strict_format"] = {
            "note": "한쪽 또는 양쪽 JSONL에 strict_format_ok 가 없어 strict 비교 생략 (Vertex eval 등).",
        }

    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output_json}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
