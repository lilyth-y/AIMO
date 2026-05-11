from __future__ import annotations

from typing import Any, Optional


def build_user_answer_explanation(
    problem_text: str | None = None,
    final_answer: str | None = None,
    orchestration_trace: list[dict[str, Any]] | None = None,
    strategy: str | None = None,
    verified: bool | None = None,
    **_kwargs: Any,
) -> Optional[str]:
    """
    Build a user-facing explanation of how the answer was produced.

    In this repo branch, the orchestration pipeline can run without XAI.
    This function is intentionally lightweight so imports do not fail.
    """
    _ = (problem_text, final_answer, orchestration_trace, strategy, verified, _kwargs)
    return None

