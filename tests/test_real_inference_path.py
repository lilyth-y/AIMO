"""
실추론 경로(로컬 HF) 단계별 스모크.

- 0단계: 코드 실행기만 (LLM 없음, 항상 실행)
- 1~3단계: ``LocalLLMClient`` → ``Solver`` → (가능하면) 실행기

HF 가중치가 필요한 테스트는 ``RUN_REAL_INFERENCE=1`` 일 때만 수행한다.
(네트워크·캐시·CPU/GPU 환경에 따라 스킵될 수 있음)

실행 예::

    set RUN_REAL_INFERENCE=1
    set AIMO_MODEL=sshleifer/tiny-gpt2
    set OMI_QUANTIZATION=none
    set AIMO_LLM_DTYPE=float32
    pytest tests/test_real_inference_path.py -v --tb=short
"""

from __future__ import annotations

import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_REPO, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# ---------------------------------------------------------------------------
# 항상: 실행 파이프 한 귀퉁이
# ---------------------------------------------------------------------------


def test_step0_code_executor_runs_trivial_print():
    from src.pipeline.stage4_execution import CodeExecutor

    ex = CodeExecutor(timeout_seconds=10)
    out = ex.execute("print(2 + 2)")
    assert isinstance(out, str)
    assert "4" in out.replace(" ", "")


def test_reset_global_llm_cache_is_callable():
    from src.pipeline.solver import reset_global_llm_cache

    reset_global_llm_cache()
    reset_global_llm_cache()


# ---------------------------------------------------------------------------
# 옵션: 실제 HF 로드 (RUN_REAL_INFERENCE=1)
# ---------------------------------------------------------------------------

TINY_DEFAULT = "sshleifer/tiny-gpt2"


def _real_inference_enabled() -> bool:
    return os.environ.get("RUN_REAL_INFERENCE", "").strip() == "1"


@pytest.fixture
def isolated_local_llm_env(monkeypatch):
    """Vertex/원격을 끄고, 소형 모델·짧은 생성으로 로컬 경로만 강제."""
    for key in (
        "GOOGLE_CLOUD_PROJECT",
        "GCP_PROJECT",
        "GOOGLE_GENAI_API_KEY",
        "VERTEX_AI_API_KEY",
        "VERTEX_AI_MODEL",
        "OMI_REMOTE_INFERENCE_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AIMO_FAST_TEST", "0")
    monkeypatch.setenv("OMI_MODEL", os.environ.get("AIMO_REAL_INFERENCE_MODEL", TINY_DEFAULT))
    monkeypatch.setenv("OMI_QUANTIZATION", "none")
    monkeypatch.delenv("MATHCODEORCHESTRATOR_QUANTIZATION", raising=False)
    monkeypatch.setenv("AIMO_LLM_DTYPE", "float32")
    monkeypatch.setenv("AIMO_MAX_NEW_TOKENS", "48")
    from src.pipeline.solver import reset_global_llm_cache

    reset_global_llm_cache()
    yield
    reset_global_llm_cache()


@pytest.mark.real_inference
@pytest.mark.skipif(not _real_inference_enabled(), reason="Set RUN_REAL_INFERENCE=1 for HF load tests")
def test_step1_local_llm_generate_returns_string(isolated_local_llm_env):
    pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from src.pipeline.solver import LocalLLMClient, reset_global_llm_cache

    reset_global_llm_cache()
    client = LocalLLMClient()
    text = client.generate("Hello", do_sample=False)
    assert isinstance(text, str)
    assert len(text) >= 0


@pytest.mark.real_inference
@pytest.mark.skipif(not _real_inference_enabled(), reason="Set RUN_REAL_INFERENCE=1 for HF load tests")
def test_step2_solver_generate_code_produces_text(isolated_local_llm_env):
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from src.pipeline.solver import Solver, reset_global_llm_cache

    reset_global_llm_cache()
    solver = Solver()
    assert getattr(solver, "_mock_solver", None) is None
    code = solver.generate_code("Compute 2+2. Output print only.", "Engineer")
    assert isinstance(code, str)
    assert len(code.strip()) > 0


@pytest.mark.real_inference
@pytest.mark.skipif(not _real_inference_enabled(), reason="Set RUN_REAL_INFERENCE=1 for HF load tests")
def test_step3_generated_code_may_run_in_executor(isolated_local_llm_env):
    """소형 모델 출력이 항상 유효 파이썬은 아니므로, 컴파일되면 실행만 검증."""
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from src.pipeline.solver import Solver, reset_global_llm_cache
    from src.pipeline.stage4_execution import CodeExecutor

    reset_global_llm_cache()
    solver = Solver()
    code = solver.generate_code("Say 1 in Python: print(1)", "Engineer")
    try:
        compile(code, "<test>", "exec")
    except SyntaxError:
        pytest.skip("tiny model did not return executable Python this run")
    ex = CodeExecutor(timeout_seconds=10)
    out = ex.execute(code)
    assert isinstance(out, str)
    assert not out.startswith("Error: Syntax error")
