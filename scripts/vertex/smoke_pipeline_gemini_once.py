"""
One-problem pipeline smoke using Vertex Gemini (real network call).

Intent:
  - Validate PipelineOrchestrator -> Solver -> Vertex Gemini path works end-to-end.
  - Keep cost low by disabling structured reasoning / refine / voting.

This script is meant for a tiny smoke only (1 problem).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]
_SRC = str(_REPO / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


def _setdefault(k: str, v: str) -> None:
    if os.getenv(k) is None:
        os.environ[k] = v


def main() -> int:
    # Minimize calls / tokens
    _setdefault("AIMO_FAST_TEST", "0")
    _setdefault("OMI_USE_STRUCTURED", "false")
    _setdefault("OMI_NUM_CANDIDATES", "1")
    _setdefault("OMI_USE_VOTING", "false")
    _setdefault("OMI_REFINE_ENABLED", "false")
    _setdefault("AIMO_VERTEX_MAX_RETRIES", "0")

    from pipeline.orchestrator import PipelineOrchestrator  # noqa: E402

    orch = PipelineOrchestrator()

    problem = os.getenv("AIMO_SMOKE_PROBLEM", "What is 2 + 2? Return only the number.")
    result = orch.solve_problem(
        domain="general_math",
        variables={},
        problem_text=problem,
        time_budget=float(os.getenv("AIMO_SMOKE_TIME_BUDGET", "20.0")),
    )

    # Print a tiny stable summary (result may contain lots of debug fields)
    answer = result.get("answer")
    method = result.get("method")
    print({"answer": answer, "method": method})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

