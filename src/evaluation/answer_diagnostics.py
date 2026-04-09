"""
평가 시점에 '채점 일치 종류'와 '추출만 잘못됐는지'를 진단한다.

- 기본 채점(is_correct)은 바꾸지 않는다.
- 결과 JSON metadata에 작은 필드만 넣어 보고·후속 실험에 쓴다.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from .evaluation_utils import (
    check_answer_correctness,
    classify_answer_match,
    normalize_answer,
    numeric_equivalent,
)

try:
    from ..pipeline.reasoning_utils import (
        extract_answer,
        extract_final_answer_from_output,
        extract_tail_answer_without_tags,
    )
except ImportError:
    from pipeline.reasoning_utils import (
        extract_answer,
        extract_final_answer_from_output,
        extract_tail_answer_without_tags,
    )

FAILURE_METHODS = frozenset(
    {
        "all_failed_rate_limited",
        "all_failed",
        "timeout",
        "worker_exception",
    }
)


def harvest_solver_output(result: Dict[str, Any], *, max_chars: int = 120_000) -> str:
    """오케스트레이터가 넘긴 dict에서 추출 후보를 뽑을 원문을 모은다."""
    chunks: List[str] = []
    for key in ("execution_result", "extracted_answer"):
        v = result.get(key)
        if isinstance(v, str) and v.strip():
            chunks.append(v.strip())
    text = "\n\n".join(chunks)
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def _dedupe_key(s: str) -> str:
    return normalize_answer(str(s))[:500]


def collect_extraction_candidates(
    predicted: Any,
    raw_text: str,
) -> List[Tuple[str, str]]:
    """
    여러 추출기로 후보를 모은다. (label, value)
    """
    out: List[Tuple[str, str]] = []
    seen: Set[str] = set()

    def add(label: str, val: Optional[str]) -> None:
        if val is None:
            return
        s = str(val).strip()
        if not s:
            return
        if s.upper().startswith("ERROR:") or s.startswith("Error:"):
            return
        k = _dedupe_key(s)
        if not k or k in seen:
            return
        seen.add(k)
        out.append((label, s))

    if predicted is not None:
        ps = str(predicted).strip()
        if ps and ps.upper() != "N/A":
            add("chosen_answer", ps)

    if raw_text.strip():
        try:
            ef = extract_final_answer_from_output(raw_text)
            add("from_final_output", ef)
        except Exception:
            pass
        try:
            ea = extract_answer(raw_text)
            if ea:
                add("from_tagged_boxed", ea)
        except Exception:
            pass
        try:
            tail = extract_tail_answer_without_tags(raw_text)
            if tail:
                add("from_tail_heuristic", tail)
        except Exception:
            pass

    return out


def _base_notation_missing_subscript(ref: str, pred: Any) -> bool:
    if not ref or pred is None:
        return False
    m = re.match(r"^(.+)_(\d+)$", str(ref).strip())
    if not m:
        return False
    core = m.group(1).strip()
    return normalize_answer(core) == normalize_answer(str(pred).strip())


def _loose_numeric_would_pass(ref: str, pred: Any) -> bool:
    if not ref or pred is None:
        return False
    if classify_answer_match(ref, pred, use_sympy=True) != "none":
        return False
    rn = normalize_answer(str(ref))
    pn = normalize_answer(str(pred))
    if not rn or not pn:
        return False
    return numeric_equivalent(rn, pn, rtol=0.05, atol=1e-5)


def infer_failure_axis(
    *,
    is_correct: bool,
    predicted: Any,
    method: str,
    alternate_would_pass: bool,
    reference: str,
) -> str:
    if is_correct:
        return "correct"

    pred_empty = predicted is None or (
        isinstance(predicted, str) and str(predicted).strip() in ("", "N/A")
    )
    if pred_empty or method in FAILURE_METHODS:
        return "pipeline_or_empty"

    if alternate_would_pass:
        return "extraction_recoverable"

    if _base_notation_missing_subscript(reference, predicted):
        return "format_or_grading"

    if _loose_numeric_would_pass(reference, predicted):
        return "format_or_grading"

    return "reasoning_likely"


def diagnose_numina_result(
    reference_answer: str,
    predicted_answer: Any,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Numina 평가 행용 진단. JSON metadata에 넣을 평탄한 dict.
    """
    ref = reference_answer or ""
    method = str(result.get("method") or "")

    pred_for_match = predicted_answer
    if isinstance(pred_for_match, str) and pred_for_match.strip().upper() == "N/A":
        pred_for_match = None
    if pred_for_match is not None and str(pred_for_match).strip() == "":
        pred_for_match = None

    match_kind: str
    if pred_for_match is None:
        match_kind = "none"
    else:
        match_kind = classify_answer_match(ref, str(pred_for_match), use_sympy=True)

    is_correct = match_kind != "none"

    raw = harvest_solver_output(result)
    candidates = collect_extraction_candidates(predicted_answer, raw)

    alternate_would_pass = False
    best_alternate_label: Optional[str] = None
    best_alternate_full: Optional[str] = None

    if not is_correct and ref:
        for label, cand in candidates:
            if label == "chosen_answer":
                continue
            try:
                if check_answer_correctness(ref, cand):
                    alternate_would_pass = True
                    best_alternate_label = label
                    best_alternate_full = cand
                    break
            except Exception:
                continue

    _max_stored = 5000
    best_alternate_answer: Optional[str] = None
    if best_alternate_full is not None:
        best_alternate_answer = (
            best_alternate_full[:_max_stored]
            if len(best_alternate_full) > _max_stored
            else best_alternate_full
        )
    preview: Optional[str] = None
    if best_alternate_answer is not None:
        preview = (
            best_alternate_answer[:200] + "…"
            if len(best_alternate_answer) > 200
            else best_alternate_answer
        )

    axis = infer_failure_axis(
        is_correct=is_correct,
        predicted=predicted_answer,
        method=method,
        alternate_would_pass=alternate_would_pass,
        reference=ref,
    )

    counterfactual_correct = is_correct or alternate_would_pass

    out: Dict[str, Any] = {
        "grading_match_kind": match_kind,
        "eval_failure_axis": axis,
        "alternate_would_pass": alternate_would_pass,
        "alternate_candidate_count": len(candidates),
        "best_alternate_source": best_alternate_label,
        "best_alternate_preview": preview,
        "counterfactual_would_pass": counterfactual_correct,
    }
    if best_alternate_answer is not None:
        out["best_alternate_answer"] = best_alternate_answer
    return out
