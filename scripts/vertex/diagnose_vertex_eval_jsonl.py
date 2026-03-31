#!/usr/bin/env python3
"""
Vertex eval JSONL 로컬 진단·비교.

- 단일 파일: 행 수, strict_format_ok / scoring_status / format_failure_reason 집계,
  predicted_answer 공백률, <ANS> 휴리스틱(지시문 이후 구간), predict_progress(failed_at·predict_calls) 등.
- --compare A B: 두 파일(예: 레거시 단발 vs 형식 게이트) 핵심 지표 나란히 출력.

예:
  python scripts/vertex/diagnose_vertex_eval_jsonl.py results/vertex_eval_old.jsonl
  python scripts/vertex/diagnose_vertex_eval_jsonl.py --compare results/legacy.jsonl results/gated.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 프로젝트 루트 (옵션: evaluation 유틸 재사용 없음)
_ROOT = Path(__file__).resolve().parents[2]


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


# 프롬프트 상단 지시문에 들어 있는 예시 <ANS>…</ANS> 와 겹치지 않게 잘라 본다.
_DEFAULT_INSTRUCTION_CUT = 220


def _tail_after_instruction(raw_head: str, cut: int) -> str:
    h = raw_head or ""
    return h[cut:] if len(h) > cut else ""


def _has_model_side_ans(raw_head: str, *, cut: int) -> bool:
    """지시문 뒤 구간에 모델이 넣은 <ANS>… 로 추정되는 태그가 있는지 (휴리스틱)."""
    tail = _tail_after_instruction(raw_head, cut)
    return bool(re.search(r"<\s*ANS\s*>", tail, re.IGNORECASE))


def _has_model_side_close_ans(raw_head: str, *, cut: int) -> bool:
    tail = _tail_after_instruction(raw_head, cut)
    return "</ANS>" in tail.upper() or "</ans>" in tail


def _accuracy_breakdowns(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """scoring_status·strict_format_ok 별 (n, correct, accuracy). eval stdout 요약과 동일 계열."""
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


def _predict_progress_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """predict_progress·error 행에서 실패 구간 요약."""
    with_pp = sum(1 for r in rows if r.get("predict_progress"))
    failed_at = Counter()
    outcome = Counter()
    call_lens: List[int] = []
    err_subs = 0
    for r in rows:
        pp = r.get("predict_progress")
        if not isinstance(pp, dict):
            continue
        fa = pp.get("failed_at")
        if fa is not None:
            failed_at[str(fa)] += 1
        oc = pp.get("outcome")
        if oc is not None:
            outcome[str(oc)] += 1
        calls = pp.get("predict_calls")
        if isinstance(calls, list):
            call_lens.append(len(calls))
            err_subs += sum(1 for c in calls if isinstance(c, dict) and not c.get("ok", True))
    n = len(rows)
    return {
        "rows_with_predict_progress": with_pp,
        "predict_progress_rate": with_pp / n if n else 0.0,
        "predict_progress_failed_at": dict(failed_at),
        "predict_progress_outcome": dict(outcome),
        "predict_calls_per_row": {
            "min": min(call_lens) if call_lens else None,
            "max": max(call_lens) if call_lens else None,
            "avg": (sum(call_lens) / len(call_lens)) if call_lens else None,
        },
        "predict_call_sub_errors_total": err_subs,
    }


def aggregate(rows: List[Dict[str, Any]], *, instruction_cut: int) -> Dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}

    pred_none = sum(1 for r in rows if r.get("predicted_answer") is None)
    correct = sum(1 for r in rows if r.get("is_correct") is True)

    has_strict = any("strict_format_ok" in r for r in rows)
    has_status = any("scoring_status" in r for r in rows)
    has_ffr = any("format_failure_reason" in r for r in rows)

    strict_c = Counter(r.get("strict_format_ok") for r in rows if "strict_format_ok" in r)
    status_c = Counter(r.get("scoring_status") for r in rows if "scoring_status" in r)
    ffr_c = Counter(r.get("format_failure_reason") for r in rows if "format_failure_reason" in r)

    model_ans = sum(
        1
        for r in rows
        if _has_model_side_ans(r.get("raw_text_head") or "", cut=instruction_cut)
    )
    model_close = sum(
        1
        for r in rows
        if _has_model_side_close_ans(r.get("raw_text_head") or "", cut=instruction_cut)
    )

    ext_fmt = Counter()
    for r in rows:
        ex = r.get("extracted")
        if isinstance(ex, dict):
            ext_fmt[str(ex.get("format"))] += 1
        else:
            ext_fmt["(missing)"] += 1

    pp_stats = _predict_progress_stats(rows)
    ab = _accuracy_breakdowns(rows)

    return {
        "n": n,
        "predicted_answer_null": pred_none,
        "predicted_answer_null_rate": pred_none / n,
        "is_correct_true": correct,
        "accuracy_reported": correct / n,
        "has_field_strict_format_ok": has_strict,
        "has_field_scoring_status": has_status,
        "has_field_format_failure_reason": has_ffr,
        "strict_format_ok_counts": dict(strict_c),
        "scoring_status_counts": dict(status_c),
        "format_failure_reason_top": ffr_c.most_common(12),
        "extracted_format_counts": dict(ext_fmt),
        "heuristic_ans_open_in_head_after_cut": model_ans,
        "heuristic_ans_open_rate_after_cut": model_ans / n,
        "heuristic_close_ans_in_head_after_cut": model_close,
        "instruction_cut_chars": instruction_cut,
        **pp_stats,
        **ab,
    }


def _fmt_report(label: str, agg: Dict[str, Any]) -> str:
    lines = [f"=== {label} ===", f"n_rows: {agg.get('n', 0)}"]
    if agg.get("n") == 0:
        return "\n".join(lines)
    lines.append(
        f"predicted_answer null: {agg['predicted_answer_null']} ({agg['predicted_answer_null_rate']:.1%})"
    )
    lines.append(f"is_correct true: {agg['is_correct_true']} (accuracy field: {agg['accuracy_reported']:.1%})")
    lines.append(
        f"fields present: strict_format_ok={agg['has_field_strict_format_ok']}, "
        f"scoring_status={agg['has_field_scoring_status']}, "
        f"format_failure_reason={agg['has_field_format_failure_reason']}"
    )
    if agg.get("strict_format_ok_counts"):
        lines.append(f"strict_format_ok: {agg['strict_format_ok_counts']}")
    if agg.get("scoring_status_counts"):
        lines.append(f"scoring_status: {agg['scoring_status_counts']}")
    if agg.get("format_failure_reason_top"):
        lines.append(f"format_failure_reason (top): {agg['format_failure_reason_top']}")
    if agg.get("extracted_format_counts"):
        lines.append(f"extracted.format: {agg['extracted_format_counts']}")
    lines.append(
        f"heuristic: <ANS> in raw_text_head after char {agg['instruction_cut_chars']}: "
        f"{agg['heuristic_ans_open_in_head_after_cut']} ({agg['heuristic_ans_open_rate_after_cut']:.1%})"
    )
    lines.append(
        f"heuristic: </ANS> in tail after cut: {agg['heuristic_close_ans_in_head_after_cut']}"
    )
    if agg.get("rows_with_predict_progress", 0):
        lines.append(
            f"predict_progress: rows={agg['rows_with_predict_progress']} "
            f"({agg['predict_progress_rate']:.1%}), failed_at={agg.get('predict_progress_failed_at')}, "
            f"outcome={agg.get('predict_progress_outcome')}"
        )
        cpr = agg.get("predict_calls_per_row") or {}
        lines.append(
            f"predict_calls/row: min={cpr.get('min')} max={cpr.get('max')} avg={cpr.get('avg')!s}, "
            f"sub_errors_total={agg.get('predict_call_sub_errors_total')}"
        )
    if agg.get("accuracy_by_scoring_status"):
        parts = []
        for k, v in sorted(agg["accuracy_by_scoring_status"].items()):
            if isinstance(v, dict):
                parts.append(
                    f"{k}={v.get('correct', 0)}/{v.get('n', 0)} "
                    f"({v.get('accuracy', 0.0):.1%})"
                )
        if parts:
            lines.append("accuracy_by_scoring_status: " + ", ".join(parts))
    if agg.get("accuracy_by_strict_format_ok"):
        b = agg["accuracy_by_strict_format_ok"]
        lines.append(
            "accuracy_by_strict_format_ok: "
            + ", ".join(
                f"{k}: n={b[k]['n']} correct={b[k]['correct']} acc={b[k]['accuracy']:.1%}"
                for k in ("true", "false")
                if k in b
            )
        )
    return "\n".join(lines)


def _compare_table(a: Dict[str, Any], b: Dict[str, Any], name_a: str, name_b: str) -> str:
    keys = [
        ("n", "rows"),
        ("predicted_answer_null_rate", "pred null rate"),
        ("accuracy_reported", "is_correct rate"),
        ("heuristic_ans_open_rate_after_cut", "<ANS> after cut (rate)"),
        ("heuristic_close_ans_in_head_after_cut", "</ANS> in head tail (count)"),
    ]
    lines = [
        f"{'metric':<36} {name_a[:28]:>28} {name_b[:28]:>28}",
        "-" * 96,
    ]
    for key, title in keys:
        va = a.get(key)
        vb = b.get(key)
        if isinstance(va, float):
            sa = f"{va:.4f}" if va is not None else "-"
        else:
            sa = str(va) if va is not None else "-"
        if isinstance(vb, float):
            sb = f"{vb:.4f}" if vb is not None else "-"
        else:
            sb = str(vb) if vb is not None else "-"
        lines.append(f"{title:<36} {sa:>28} {sb:>28}")
    lines.append("")
    lines.append(
        f"{'has scoring_status field':<36} {str(a.get('has_field_scoring_status')):>28} "
        f"{str(b.get('has_field_scoring_status')):>28}"
    )
    lines.append(
        f"{'has strict_format_ok field':<36} {str(a.get('has_field_strict_format_ok')):>28} "
        f"{str(b.get('has_field_strict_format_ok')):>28}"
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Vertex eval JSONL 로컬 진단·비교")
    ap.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="단일 JSONL 경로",
    )
    ap.add_argument(
        "--compare",
        nargs=2,
        metavar=("LEGACY", "GATED"),
        help="두 JSONL 비교 (예: 레거시 단발 vs 형식 게이트)",
    )
    ap.add_argument(
        "--instruction-cut",
        type=int,
        default=_DEFAULT_INSTRUCTION_CUT,
        help=f"지시문·예시 <ANS>와 구분하기 위한 앞부분 제거 글자 수 (기본 {_DEFAULT_INSTRUCTION_CUT})",
    )
    args = ap.parse_args()

    if args.compare:
        pa, pb = Path(args.compare[0]), Path(args.compare[1])
        if not pa.is_file() or not pb.is_file():
            print("ERROR: 파일이 없습니다.", pa, pb, file=sys.stderr)
            return 1
        ra, rb = _load_rows(pa), _load_rows(pb)
        aa = aggregate(ra, instruction_cut=args.instruction_cut)
        ab = aggregate(rb, instruction_cut=args.instruction_cut)
        print(_fmt_report(str(pa), aa))
        print()
        print(_fmt_report(str(pb), ab))
        print()
        print(_compare_table(aa, ab, pa.name, pb.name))
        return 0

    if not args.path:
        ap.print_help()
        return 2
    p = Path(args.path)
    if not p.is_file():
        print("ERROR: 파일 없음:", p, file=sys.stderr)
        return 1
    rows = _load_rows(p)
    agg = aggregate(rows, instruction_cut=args.instruction_cut)
    print(_fmt_report(str(p), agg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
