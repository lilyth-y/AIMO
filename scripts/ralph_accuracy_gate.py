#!/usr/bin/env python3
"""
Exit 0 if saved evaluation JSON meets Ralph accuracy target; else exit 1.

Usage:
  python scripts/ralph_accuracy_gate.py results/some_eval_results.json
  python scripts/ralph_accuracy_gate.py --json results/foo.json

Env:
  AIMO_RALPH_TARGET_ACCURACY_PCT  (default: 80, or floor of TARGET_ACCURACY_EASY)
  AIMO_RALPH_GATE_MODE            overall | easy
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.ralph_accuracy import evaluate_gate_from_saved_dict  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Ralph accuracy gate on EvaluationMetrics JSON")
    p.add_argument("json_path", nargs="?", help="Path to *results*.json from save_results")
    p.add_argument("--json", dest="json_path_opt", help="Same as positional")
    args = p.parse_args()
    path = args.json_path or args.json_path_opt
    if not path:
        p.error("Provide a JSON path")
    fp = Path(path)
    if not fp.is_file():
        print(f"FAIL: file not found: {fp}", file=sys.stderr)
        return 1
    with fp.open(encoding="utf-8") as f:
        data = json.load(f)
    ok, msg, observed, target = evaluate_gate_from_saved_dict(data)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
