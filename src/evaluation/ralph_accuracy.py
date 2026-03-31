"""
Ralph loop (Cursor) completion criteria for **accuracy** optimization.

- Default target: **80%** overall accuracy (same floor as ``TARGET_ACCURACY_EASY`` min).
- Override: ``AIMO_RALPH_TARGET_ACCURACY_PCT`` (e.g. ``82.5``).
- Gate mode: ``AIMO_RALPH_GATE_MODE`` = ``overall`` | ``easy`` (stratified easy bucket only).

Grading uses the same rule as evaluations: ``check_answer_correctness`` → ``EvaluationMetrics`` summary.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Literal, Tuple

from .config import RALPH_TARGET_ACCURACY_DEFAULT_PCT

GateMode = Literal["overall", "easy"]


def ralph_target_accuracy_pct() -> float:
    """Primary scalar target for pass/fail (default 80.0)."""
    raw = os.getenv("AIMO_RALPH_TARGET_ACCURACY_PCT")
    if raw is None or str(raw).strip() == "":
        return RALPH_TARGET_ACCURACY_DEFAULT_PCT
    return float(raw)


def ralph_gate_mode() -> GateMode:
    m = (os.getenv("AIMO_RALPH_GATE_MODE") or "overall").strip().lower()
    if m in ("easy", "overall"):
        return m  # type: ignore[return-value]
    return "overall"


def extract_accuracy_from_saved_eval(data: Dict[str, Any]) -> Tuple[float, str]:
    """
    Read accuracy from JSON written by ``EvaluationMetrics.save_results`` (``summary`` block)
    or a flat metrics dict (``accuracy`` key).
    """
    if "summary" in data and isinstance(data["summary"], dict):
        summary = data["summary"]
        label = "summary.accuracy"
    else:
        summary = data
        label = "accuracy"

    acc = summary.get("accuracy")
    if acc is None:
        raise ValueError("No 'accuracy' in evaluation JSON (expected summary.accuracy).")
    return float(acc), label


def extract_easy_accuracy_from_saved_eval(data: Dict[str, Any]) -> Tuple[float, str]:
    """``by_difficulty.easy.accuracy`` from saved eval summary."""
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else data
    bd = summary.get("by_difficulty") or {}
    easy = bd.get("easy")
    if not isinstance(easy, dict) or easy.get("accuracy") is None:
        raise ValueError("No easy bucket in by_difficulty (need problems labeled easy).")
    return float(easy["accuracy"]), "summary.by_difficulty.easy.accuracy"


def meets_ralph_target(observed_pct: float, *, target_pct: float | None = None) -> bool:
    if target_pct is None:
        target_pct = ralph_target_accuracy_pct()
    return observed_pct + 1e-9 >= target_pct


def vertex_summary_accuracy_to_observed_pct(summary: Dict[str, Any]) -> Tuple[float, str]:
    """
    ``eval_vertex_endpoint_quality.py`` summary uses ``accuracy`` in [0, 1].
    If value > 1, treat as already percent (0–100).
    """
    raw = summary.get("accuracy")
    if raw is None:
        raise ValueError("No 'accuracy' in Vertex eval summary.")
    v = float(raw)
    if v <= 1.0 + 1e-9:
        return v * 100.0, "summary.accuracy(fraction->pct)"
    return v, "summary.accuracy(percent)"


def evaluate_vertex_summary_for_ralph(summary: Dict[str, Any]) -> Tuple[bool, str, float, float]:
    """
    Ralph gate on Vertex Custom Job / ``eval_vertex_endpoint_quality`` summary dict.
    """
    target = ralph_target_accuracy_pct()
    observed, path = vertex_summary_accuracy_to_observed_pct(summary)
    ok = meets_ralph_target(observed, target_pct=target)
    msg = f"vertex {path}={observed:.2f}% (target >= {target:.2f}%)"
    if ok:
        msg = "PASS: " + msg
    else:
        msg = "FAIL: " + msg
    return ok, msg, observed, target


def evaluate_gate_from_saved_dict(data: Dict[str, Any]) -> Tuple[bool, str, float, float]:
    """
    Returns (pass, message, observed, target).
    """
    target = ralph_target_accuracy_pct()
    mode = ralph_gate_mode()
    if mode == "easy":
        observed, path = extract_easy_accuracy_from_saved_eval(data)
        msg = f"easy {path}={observed:.2f}% (target >= {target:.2f}%)"
    else:
        observed, path = extract_accuracy_from_saved_eval(data)
        msg = f"overall {path}={observed:.2f}% (target >= {target:.2f}%)"

    ok = meets_ralph_target(observed, target_pct=target)
    if ok:
        msg = "PASS: " + msg
    else:
        msg = "FAIL: " + msg
    return ok, msg, observed, target
