"""
One-shot Gemini (Vertex) smoke test.

This DOES make a single network call to Vertex Gemini via google-genai.
Keep prompts tiny to minimize cost/latency.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SRC = str(_REPO / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from pipeline.vertex_inference import generate_vertex  # noqa: E402


def main() -> int:
    prompt = os.getenv("AIMO_SMOKE_PROMPT", "Return ONLY the word OK.")
    text = generate_vertex(prompt)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

