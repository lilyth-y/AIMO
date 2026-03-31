"""
<ANS>...</ANS> 형식 검증 및 재시도용 프롬프트.

- 채점에 앞서 **단일 비어 있지 않은** ANS 블록이 있는지 검사한다.
- 여러 개의 <ANS> 블록이 있으면(모호성) strict 모드에서 실패 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# non-greedy inner (빈 태그는 매칭되나 validate에서 EMPTY_ANS); case-insensitive tags
_ANS_BLOCK_RE = re.compile(
    r"<ANS>\s*(.*?)\s*</ANS>",
    re.IGNORECASE | re.DOTALL,
)
_ANS_OPEN_RE = re.compile(r"<ANS\s*>", re.IGNORECASE)


@dataclass(frozen=True)
class AnsFormatValidation:
    ok: bool
    reason: Optional[str]  # None if ok
    inner_content: Optional[str]


def validate_ans_strict(
    completion_text: str,
    *,
    single_block_only: bool = True,
) -> AnsFormatValidation:
    """
    생성 **연속 구간**(프롬프트 제외)만 검사한다.

    Args:
        completion_text: 모델 연속 출력
        single_block_only: True면 <ANS> 여는 태그가 2개 이상이면 MULTIPLE_ANS_BLOCKS
    """
    if not completion_text or not completion_text.strip():
        return AnsFormatValidation(False, "EMPTY_COMPLETION", None)

    if single_block_only:
        opens = _ANS_OPEN_RE.findall(completion_text)
        if len(opens) > 1:
            return AnsFormatValidation(False, "MULTIPLE_ANS_BLOCKS", None)

    m = _ANS_BLOCK_RE.search(completion_text)
    if not m:
        return AnsFormatValidation(False, "NO_ANS_TAG", None)

    inner = (m.group(1) or "").strip()
    if not inner:
        return AnsFormatValidation(False, "EMPTY_ANS", None)

    return AnsFormatValidation(True, None, inner)


def build_format_repair_prompt(problem_text: str) -> str:
    """형식 실패 후 재시도용: 설명 없이 ANS만 강제."""
    return (
        "OUTPUT RULE (mandatory):\n"
        "- Respond with EXACTLY one block: <ANS>final answer here</ANS>\n"
        "- No proof, no steps, no text before or after that block.\n\n"
        f"Problem:\n{problem_text.strip()}\n"
    )


def build_prompt_strict_first(problem_text: str) -> str:
    """첫 시도용: 기존 지시보다 형식을 더 강하게 고정."""
    return (
        "You are solving a math problem.\n"
        "Your ENTIRE response must be ONLY:\n"
        "<ANS>final answer here</ANS>\n"
        "Nothing else. No explanation.\n\n"
        f"Problem:\n{problem_text.strip()}\n"
    )


def build_verification_agent_prompt(
    problem_text: str,
    model_output: str,
    *,
    max_chars: int = 12000,
) -> str:
    """
    형식 미준수·노이즈 출력을 **검수(정리)**할 때 쓰는 2차 프롬프트.

    이전 생성문에서 최종 답만 뽑아 단일 <ANS>...</ANS> 로만 응답하도록 요구한다.
    """
    prev = (model_output or "").strip()
    if len(prev) > max_chars:
        prev = prev[:max_chars] + "\n...[truncated for verification context]\n"

    return (
        "You are a verification agent. Read the problem and the prior model's output.\n"
        "Extract ONLY the final answer that should be graded.\n\n"
        "OUTPUT RULE (mandatory):\n"
        "- Your ENTIRE response must be EXACTLY one block: <ANS>final answer here</ANS>\n"
        "- Put only the final answer inside the tags (LaTeX is allowed, e.g. \\frac{1}{3}).\n"
        "- No proof, no steps, no text before or after that block.\n"
        "- If the prior output is incomplete or contradictory, infer the best single final answer.\n\n"
        f"Problem:\n{problem_text.strip()}\n\n"
        f"Prior model output:\n{prev}\n"
    )
