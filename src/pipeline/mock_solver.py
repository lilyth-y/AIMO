"""
테스트·CI용 결정론적 Mock (HF/Vertex 없이 파이프라인 골격만 돌릴 때 사용).

이 모듈은 **문제를 풀지 않습니다.** ``AIMO_MOCK_GENERATED_CODE`` 로 고정한 코드만
반환합니다. 검증 대상은 다음뿐입니다.

- 코드 실행기(CodeExecutor)가 돌아가는지
- 답 추출·오케스트레이터 반환 dict 계약이 유지되는지
- (선택) 라우팅/폴백이 예외 없이 이어지는지

수학적 정답률·난이도별 성능은 **실제 모델/엔드포인트 평가**로만 측정해야 합니다.
"""

import os

from .logger import get_logger

logger = get_logger()

# 실행 가능한 한 줄(또는 세미콜론으로 이은 짧은 블록) 권장. 기본은 0.
_DEFAULT_MOCK_CODE = "print(0)"
_ENV_MOCK_CODE = "AIMO_MOCK_GENERATED_CODE"


def get_configured_mock_code() -> str:
    """환경 변수로 주입된 코드만 반환. 비어 있으면 기본 ``print(0)``."""
    raw = os.getenv(_ENV_MOCK_CODE, _DEFAULT_MOCK_CODE)
    if isinstance(raw, str):
        raw = raw.strip()
    if not raw:
        return _DEFAULT_MOCK_CODE
    return raw


class MockLLMClient:
    """프롬프트 내용과 무관하게 설정된 코드 문자열만 돌려준다 (하이브리드 등 ``llm.generate`` 호출용)."""

    def __init__(self):
        logger.debug("MockLLMClient initialized (deterministic, no model)")

    def generate(self, prompt: str, **kwargs) -> str:
        del prompt, kwargs
        return get_configured_mock_code()


class MockSolver:
    """Solver 대체용: ``generate_code`` 가 항상 ``get_configured_mock_code()`` 결과를 쓴다."""

    def __init__(self):
        self.llm = MockLLMClient()
        self.last_reasoning = None
        self.last_syntax_error = False

    def generate_code(self, problem_text: str, strategy: str) -> str:
        del problem_text
        code = get_configured_mock_code()
        self.last_reasoning = (
            f"<PLAN>deterministic_mock env={_ENV_MOCK_CODE!r} strategy={strategy!r}</PLAN>\n"
            f"<ANS>{code}</ANS>"
        )
        return code
