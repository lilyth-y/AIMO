"""Metadata-based stratified metrics (problem_type / question_type)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from evaluation.evaluation_utils import (
    EvaluationMetrics,
    EvaluationResult,
    mcnemar_exact_two_sided_p_value,
    stratified_mcnemar_paired_ab,
)


def test_by_problem_type_and_question_type():
    m = EvaluationMetrics(dataset_name="strata_test")
    m.add_result(
        EvaluationResult(
            problem_id=0,
            problem="p0",
            is_correct=True,
            metadata={"problem_type": "Algebra", "question_type": "math-word-problem"},
        )
    )
    m.add_result(
        EvaluationResult(
            problem_id=1,
            problem="p1",
            is_correct=False,
            metadata={"problem_type": "Algebra", "question_type": "math-word-problem"},
        )
    )
    m.add_result(
        EvaluationResult(
            problem_id=2,
            problem="p2",
            is_correct=True,
            metadata={"problem_type": "Geometry", "question_type": "proof"},
        )
    )
    m.add_result(
        EvaluationResult(
            problem_id=3,
            problem="p3",
            is_correct=False,
            metadata={},
        )
    )
    out = m.calculate_metrics()
    assert out["by_problem_type"]["Algebra"]["total"] == 2
    assert out["by_problem_type"]["Algebra"]["correct"] == 1
    assert abs(out["by_problem_type"]["Algebra"]["accuracy"] - 50.0) < 1e-6
    assert out["by_problem_type"]["Geometry"]["accuracy"] == 100.0
    assert out["by_problem_type"]["unknown"]["total"] == 1

    assert out["by_question_type"]["math-word-problem"]["total"] == 2
    assert out["by_question_type"]["proof"]["correct"] == 1
    assert out["by_question_type"]["unknown"]["total"] == 1

    assert out["by_easy_stratum"]["unknown"]["total"] == 4


def test_empty_metrics_has_strata_keys():
    m = EvaluationMetrics(dataset_name="empty")
    out = m.calculate_metrics()
    assert out["by_problem_type"] == {}
    assert out["by_question_type"] == {}
    assert out["by_easy_stratum"] == {}


def test_mcnemar_exact_symmetric_discordant():
    assert mcnemar_exact_two_sided_p_value(5, 5) == 1.0
    assert mcnemar_exact_two_sided_p_value(0, 0) == 1.0


def test_stratified_mcnemar_paired_ab():
    paired = [
        {
            "problem_type": "Algebra",
            "baseline": {"is_correct": True},
            "treatment": {"is_correct": False},
        },
        {
            "problem_type": "Algebra",
            "baseline": {"is_correct": False},
            "treatment": {"is_correct": True},
        },
        {
            "problem_type": "Geometry",
            "baseline": {"is_correct": True},
            "treatment": {"is_correct": True},
        },
    ]
    out = stratified_mcnemar_paired_ab(paired, "problem_type")
    assert out["stratum_key"] == "problem_type"
    alg = out["strata"]["Algebra"]
    assert alg["discordant_n"] == 2
    assert alg["baseline_only_correct"] == 1 and alg["treatment_only_correct"] == 1
    assert alg["mcnemar_exact_p_value"] == 1.0
    geo = out["strata"]["Geometry"]
    assert geo["discordant_n"] == 0
    assert geo["mcnemar_exact_p_value"] == 1.0
