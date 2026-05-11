"""
Stage 2: Domain Experts Retrieval
- Dynamic Context Loading based on domain
"""

from __future__ import annotations

from typing import Callable, Optional


class ContextLoader:
    def __init__(self):
        self.contexts = {
            "Geometry": "import shapely\nimport sympy.geometry\n# Use coordinate geometry...",
            "Number Theory": "from sympy.ntheory import factorint, totient\n# Use modular arithmetic...",
            "Combinatorics": "import itertools\nfrom scipy.special import comb\n# Use DP or counting...",
            "Algebra": "from sympy import symbols, solve, expand, factor\n# Use symbolic manipulation..."
        }

    def get_context(self, domain: str) -> str:
        return self.contexts.get(domain, "# No specific context loaded")


class KnowledgeGroundRetriever:
    """
    Deterministic "prior knowledge" injection used by the orchestrator.

    The goal is to supply short, safe, domain-relevant snippets that improve
    code-generation prompts. This stage is intentionally lightweight and should
    never fail the solve if no context matches.
    """

    def __init__(self) -> None:
        self._loader = ContextLoader()

    def retrieve(
        self,
        domain: str,
        problem_type: str,
        problem_text: str,
        add_trace: Optional[Callable[[str, str, str], None]] = None,
    ) -> str:
        _ = (problem_type, problem_text)
        try:
            ctx = self._loader.get_context(domain)
            # Treat the fallback as "no context".
            if ctx.strip() == "# No specific context loaded":
                ctx = ""
            if add_trace is not None:
                add_trace("stage2_retrieval", "ok", f"domain={domain or 'unknown'} chars={len(ctx)}")
            return ctx
        except Exception as e:
            if add_trace is not None:
                add_trace("stage2_retrieval", "error", f"{type(e).__name__}: {e}")
            return ""


if __name__ == "__main__":
    # Example usage
    loader = ContextLoader()
    # print(loader.get_context("Number Theory"))
