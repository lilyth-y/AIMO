#!/usr/bin/env python3
"""
Ralph accuracy gate for Vertex ``eval_vertex_endpoint_quality.py`` summary JSON.

The summary uses ``accuracy`` in [0, 1] (fraction). Target is percent (default 80).

Usage:
  python scripts/vertex/ralph_vertex_accuracy_gate.py /tmp/vertex_summary.json

Env:
  AIMO_RALPH_TARGET_ACCURACY_PCT  (default 80)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from evaluation.ralph_accuracy import evaluate_vertex_summary_for_ralph  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Ralph gate on Vertex eval summary JSON")
    p.add_argument("summary_json", help="JSON file: eval_vertex_endpoint_quality summary dict")
    args = p.parse_args()
    fp = Path(args.summary_json)
    if not fp.is_file():
        print(f"FAIL: not found: {fp}", file=sys.stderr)
        return 1
    with fp.open(encoding="utf-8") as f:
        summary = json.load(f)
    ok, msg, _, _ = evaluate_vertex_summary_for_ralph(summary)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
