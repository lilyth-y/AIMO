#!/usr/bin/env python3
"""
Ralph Loop — Tier 3 smoke (tiered eval: small real pipeline → saved JSON → accuracy gate).

Tier mapping (user rules + ralph-loop.mdc):
  Tier 1: execution / wiring (covered by scripts/ralph_local_verify.py).
  Tier 2: gate on fixture (CI + local verify).
  Tier 3: **this script** — run a *small* Numina eval, write ``results/*_results.json``,
          run ``scripts/ralph_accuracy_gate.py`` on that file.

Default: ``AIMO_FAST_TEST=1``, ``MAX_PROBLEMS=3``
  - Mock solver → accuracy ~0%; gate at 80% **must FAIL** (exit 1).
  - This script exits 0 when: eval succeeds **and** gate exits 1 (honest failure).

``--real``: do not set ``AIMO_FAST_TEST`` (loads HF model; slow, needs RAM/GPU).
  - This script exits 0 iff eval succeeds **and** gate exits 0 (target ≥80%).

One variable per experiment: change only one of model / voting / MAX_PROBLEMS / fast_test per run.

Usage:
  python scripts/ralph_tier3_numina_smoke.py
  python scripts/ralph_tier3_numina_smoke.py --real --problems 2
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], env: dict) -> int:
    print("\n$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    return int(r.returncode)


def main() -> int:
    p = argparse.ArgumentParser(description="Ralph Tier 3 Numina smoke (eval JSON + gate)")
    p.add_argument("--real", action="store_true", help="Real HF path (no AIMO_FAST_TEST); slow")
    p.add_argument("--problems", type=int, default=3, help="MAX_PROBLEMS (default 3)")
    args = p.parse_args()
    use_fast = not args.real

    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    if use_fast:
        env["AIMO_FAST_TEST"] = "1"
    else:
        env.pop("AIMO_FAST_TEST", None)
    env["MAX_PROBLEMS"] = str(max(1, args.problems))

    eval_py = ROOT / "examples" / "run_numina_evaluation.py"
    gate_py = ROOT / "scripts" / "ralph_accuracy_gate.py"
    results_json = ROOT / "results" / "numina_eval_balanced_results.json"

    print("=" * 70, flush=True)
    print("Ralph Tier 3: Numina smoke → results JSON → ralph_accuracy_gate", flush=True)
    print(f"  fast_mock={use_fast}  MAX_PROBLEMS={env['MAX_PROBLEMS']}", flush=True)
    print("=" * 70, flush=True)

    if _run([sys.executable, str(eval_py)], env=env) != 0:
        print("FAIL: Numina evaluation subprocess failed", flush=True, file=sys.stderr)
        return 1

    if not results_json.is_file():
        print("FAIL: expected results at", results_json, flush=True, file=sys.stderr)
        return 1

    gate_rc = _run([sys.executable, str(gate_py), str(results_json)], env=os.environ)
    if use_fast:
        if gate_rc != 1:
            print(
                "FAIL: expected ralph_accuracy_gate to exit 1 (mock ~0%% acc vs 80%% target), "
                f"got exit {gate_rc}",
                flush=True,
                file=sys.stderr,
            )
            return 1
        print(
            "\nPASS: Tier 3 smoke — eval artifact written and gate correctly FAIL "
            "(disable AIMO_FAST_TEST for real accuracy work; one variable per experiment).",
            flush=True,
        )
    else:
        if gate_rc != 0:
            print(
                f"FAIL: --real mode expected gate exit 0, got {gate_rc}",
                flush=True,
                file=sys.stderr,
            )
            return 1
        print("\nPASS: Tier 3 — eval + gate both passed (--real).", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
