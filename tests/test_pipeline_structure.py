"""
파이프라인 구조·공개 계약(solve_problem 반환 형태)·평가 메트릭 완성도 유닛 테스트.

실제 HF 모델 로드/추론은 피하기 위해 ``Solver.generate_code`` 를 패치하는 경우가 있다.
"""

from __future__ import annotations

import inspect
import os
import sys

import pytest

pytestmark = pytest.mark.structure

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_REPO, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# 최소 계약: orchestrator.solve_problem 이 항상 포함해야 할 키
REQUIRED_SOLVE_KEYS = frozenset({"answer", "method"})


@pytest.fixture
def orchestrator():
    from src.pipeline.orchestrator import PipelineOrchestrator

    return PipelineOrchestrator()


def test_core_pipeline_imports():
    from src.pipeline import config as pipeline_config
    from src.pipeline.orchestrator import PipelineOrchestrator
    from src.pipeline.solver import Solver
    from src.pipeline.stage3_router import CalculationRouter
    from src.pipeline.stage4_execution import CodeExecutor
    from src.pipeline.stage5_verification import VerificationRouter
    from src.pipeline.reconciliation import ReasoningReconciler
    from src.pipeline.refine_loop import create_refine_loop

    assert pipeline_config is not None
    assert all(
        x is not None
        for x in (
            PipelineOrchestrator,
            Solver,
            CalculationRouter,
            CodeExecutor,
            VerificationRouter,
            ReasoningReconciler,
            create_refine_loop,
        )
    )


def test_orchestrator_subcomponents_wired(orchestrator):
    o = orchestrator
    assert o.router is not None
    assert o.executor is not None
    assert o.verifier is not None
    assert o.reconciler is not None
    assert o.solver is not None
    assert o.decomposer is not None
    assert o.geo_solver is not None
    assert o.hybrid_engine is not None
    assert o.refine_loop is not None
    assert o.problem_analyzer is not None
    assert callable(getattr(o.solver, "generate_code", None))


def test_solve_problem_signature():
    from src.pipeline.orchestrator import PipelineOrchestrator

    sig = inspect.signature(PipelineOrchestrator.solve_problem)
    names = set(sig.parameters)
    assert {"domain", "variables", "problem_text"}.issubset(names)


def test_solve_problem_return_contract_with_patched_code(orchestrator):
    """LLM 없이 코드 생성만 고정해 파이프라인이 dict 계약을 지키는지 확인."""
    orch = orchestrator
    orch.solver.generate_code = lambda problem_text, strategy: "print(42)"

    result = orch.solve_problem(
        "general_math",
        {},
        "What is 15 + 27?",
        time_budget=15.0,
    )
    assert isinstance(result, dict)
    missing = REQUIRED_SOLVE_KEYS - result.keys()
    assert not missing, f"missing keys: {missing}"


def test_mock_solver_emits_configured_code_only(monkeypatch):
    """Mock은 문제 텍스트와 무관하게 환경 변수로 고정된 코드만 낸다."""
    monkeypatch.setenv("AIMO_MOCK_GENERATED_CODE", "print(99)")
    from src.pipeline.mock_solver import MockSolver

    m = MockSolver()
    assert m.generate_code("any problem text", "direct") == "print(99)"
    assert m.llm.generate("ignored prompt") == "print(99)"


def test_refine_loop_factory():
    from src.pipeline.refine_loop import create_refine_loop

    loop = create_refine_loop(max_iterations=2, enable_loop=True)
    assert loop is not None
    assert loop.max_iterations == 2
    assert callable(loop.should_refine)


def test_evaluation_metrics_contract_completeness():
    from evaluation.evaluation_utils import EvaluationMetrics, EvaluationResult

    m = EvaluationMetrics("structure_test")
    m.add_result(
        EvaluationResult(
            problem_id=0,
            problem="p",
            is_correct=True,
            difficulty="easy",
            source="gsm8k",
            metadata={"problem_type": "Algebra", "question_type": "math-word-problem"},
        )
    )
    s = m.calculate_metrics()
    for key in (
        "total",
        "correct",
        "accuracy",
        "by_difficulty",
        "by_source",
        "by_method",
        "by_problem_type",
        "by_question_type",
    ):
        assert key in s, f"summary missing {key}"


def test_settings_surface():
    from src.pipeline.settings import settings

    assert isinstance(settings.model_name, str) and len(settings.model_name) > 0
    assert isinstance(settings.refine_enabled, bool)


def test_aimo_fast_test_solver_uses_mock(monkeypatch):
    monkeypatch.setenv("AIMO_FAST_TEST", "1")
    monkeypatch.setenv("AIMO_MOCK_GENERATED_CODE", "print(42)")
    from src.pipeline.solver import Solver

    s = Solver()
    assert getattr(s, "_mock_solver", None) is not None
    assert s.generate_code("irrelevant problem", "Engineer") == "print(42)"


def test_aimo_fast_test_orchestrator_solve_smoke(monkeypatch):
    """
    목적: 실제 LLM 없이 실행·추출·반환 계약만 확인 (답 42는 환경으로 주입한 print 결과).
    """
    monkeypatch.setenv("AIMO_FAST_TEST", "1")
    monkeypatch.setenv("AIMO_MOCK_GENERATED_CODE", "print(42)")
    from src.pipeline.orchestrator import PipelineOrchestrator

    orch = PipelineOrchestrator()
    result = orch.solve_problem(
        "general_math",
        {},
        "This text does not matter for the mock.",
        time_budget=20.0,
    )
    assert isinstance(result, dict)
    assert REQUIRED_SOLVE_KEYS.issubset(result.keys())
    assert result.get("method") != "all_failed", result
    assert str(result.get("answer", "")).strip() in ("42", "42.0")
