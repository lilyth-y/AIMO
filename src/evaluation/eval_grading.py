"""
Eval 스크립트(Vertex/HF) 공통: 완성문에서 정답 추출·채점 경로.

- format_ok: <ANS> 단일 블록 strict 통과 시 `extract_from_text`만 사용.
- 그렇지 않고 fallback_boxed: 마지막 \\boxed{} → ANS 재추출 → (선택) tail 휴리스틱.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from evaluation.evaluation_utils import check_answer_correctness
from pipeline.answer_extraction import AnswerExtractor


def extract_boxed_last_simple(text: str) -> Optional[str]:
    """마지막 \\boxed{...} 내부 문자열 (단순 비중첩). 없으면 None."""
    if not text:
        return None
    found = re.findall(r"\\boxed\{([^}]*)\}", text)
    if not found:
        return None
    inner = (found[-1] or "").strip()
    return inner if inner else None


def grade_completion_for_eval(
    reference_answer: str,
    text: str,
    *,
    format_ok: bool,
    fallback_boxed: bool,
    last_resort: bool,
    extractor: AnswerExtractor,
) -> Tuple[Optional[str], bool, str, Dict[str, Any]]:
    """
    Returns: (pred_str, is_correct, scoring_status, extracted_meta)

    extracted_meta에는 항상 extraction_route 포함:
    ans_tag | no_ans_tag | ans_tag_empty | boxed_fallback | ans_tag_fallback |
    last_resort_tail | extract_failed | skipped
    """
    ext_skipped: Dict[str, Any] = {
        "value": None,
        "format": "SKIPPED",
        "confidence": 0.0,
        "error": None,
        "extraction_route": "skipped",
    }

    def _meta(ext: Any, route: str) -> Dict[str, Any]:
        return {
            "value": getattr(ext, "value", None),
            "format": getattr(ext, "format", None),
            "confidence": getattr(ext, "confidence", 0.0),
            "error": getattr(ext, "error", None),
            "extraction_route": route,
        }

    if format_ok:
        ext = extractor.extract_from_text(text or "")
        pred_val = ext.value
        if pred_val is Ellipsis:
            pred_val = None
        pred_str = str(pred_val) if pred_val is not None else None
        if ext.format == "NOT_FOUND":
            route = "no_ans_tag"
        elif ext.format == "EMPTY":
            route = "ans_tag_empty"
        else:
            route = "ans_tag"
        ok = bool(check_answer_correctness(reference_answer, pred_str))
        return pred_str, ok, "graded", _meta(ext, route)

    if not fallback_boxed:
        return None, False, "skipped_invalid_format", ext_skipped

    boxed = extract_boxed_last_simple(text or "")
    if boxed is not None:
        ok = bool(check_answer_correctness(reference_answer, boxed))
        return boxed, ok, "graded_fallback", {
            "value": boxed,
            "format": "BOXED_FALLBACK",
            "confidence": 0.5,
            "error": None,
            "extraction_route": "boxed_fallback",
        }

    ext = extractor.extract_from_text(text or "")
    pred_val = ext.value
    if pred_val is Ellipsis:
        pred_val = None
    pred_str = str(pred_val) if pred_val is not None else None
    if pred_str:
        ok = bool(check_answer_correctness(reference_answer, pred_str))
        return pred_str, ok, "graded_fallback", _meta(ext, "ans_tag_fallback")

    if last_resort:
        from pipeline.reasoning_utils import extract_tail_answer_without_tags

        tail = extract_tail_answer_without_tags(text or "")
        if tail:
            ok = bool(check_answer_correctness(reference_answer, tail))
            return tail, ok, "graded_fallback", {
                "value": tail,
                "format": "LAST_RESORT_TAIL",
                "confidence": 0.35,
                "error": None,
                "extraction_route": "last_resort_tail",
            }

    return None, False, "skipped_invalid_format", {
        "value": None,
        "format": ext.format,
        "confidence": ext.confidence,
        "error": ext.error,
        "extraction_route": "extract_failed",
    }
