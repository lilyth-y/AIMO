"""answer_diagnostics: 추론 vs 추출 분리 진단."""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def _no_vertex(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GCP_PROJECT", raising=False)


def test_diagnose_correct_match_kind():
    from evaluation.answer_diagnostics import diagnose_numina_result

    r = diagnose_numina_result(
        "223",
        "223",
        {"method": "Path A: The Simulator", "execution_result": "223", "extracted_answer": None},
    )
    assert r["grading_match_kind"] != "none"
    assert r["eval_failure_axis"] == "correct"
    assert r["alternate_would_pass"] is False


def test_extraction_recoverable_when_body_has_answer():
    from evaluation.answer_diagnostics import diagnose_numina_result

    # 최종 chosen 는 틀렸지만 본문에 정답이 있음
    body = """Some reasoning...
Final answer line
Answer: 223
"""
    r = diagnose_numina_result(
        "223",
        "5",
        {
            "method": "Path A: The Simulator",
            "execution_result": body,
            "extracted_answer": None,
        },
    )
    assert r["eval_failure_axis"] == "extraction_recoverable"
    assert r["alternate_would_pass"] is True
    assert r["counterfactual_would_pass"] is True
    assert r.get("best_alternate_answer")
    assert "223" in r["best_alternate_answer"]


def test_pipeline_empty():
    from evaluation.answer_diagnostics import diagnose_numina_result

    r = diagnose_numina_result(
        "1",
        None,
        {"method": "all_failed_rate_limited", "execution_result": "", "extracted_answer": None},
    )
    assert r["eval_failure_axis"] == "pipeline_or_empty"
    assert r["grading_match_kind"] == "none"


def test_format_base_subscript():
    from evaluation.answer_diagnostics import diagnose_numina_result

    r = diagnose_numina_result(
        "1000_7",
        "1000",
        {
            "method": "Path A: The Simulator",
            "execution_result": "1000",
            "extracted_answer": None,
        },
    )
    assert r["eval_failure_axis"] == "format_or_grading"
    assert r["alternate_would_pass"] is False
