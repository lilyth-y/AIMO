#!/usr/bin/env python3
"""
Ralph Loop — local completion checklist (aligned with .cursor/rules/ralph-loop.mdc).

Completion criteria addressed here (automated):
  • Test-driven loop: full pytest green (CI parity: PYTHONPATH=src).
  • Tiered eval (user rules 1→2→3): Tier 1 execution smoke; Tier 2 data/eval wiring;
    Tier 3 = real benchmark + scripts/ralph_accuracy_gate.py on *your* results JSON
    (not run here — needs GPU/time; see docs/run-eval/).
  • Accuracy gate: scripts/ralph_accuracy_gate.py exits 0 on a committed fixture
    (default target AIMO_RALPH_TARGET_ACCURACY_PCT / 80%).
  • RefineLoop: import-only smoke (orchestrator-related pattern in ralph-loop rule).

One-variable rule: when tuning accuracy, change only one of
  AIMO_OPTIMIZE_ACCURACY, OMI_USE_VOTING, OMI_NUM_CANDIDATES, OMI_MODEL, … per run.

Exit 0 if all steps pass; else 1.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, env: dict | None = None) -> int:
    print("\n$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=env)
    return int(r.returncode)


def main() -> int:
    banner = (
        __doc__
        + "\n"
        + "=" * 70
        + "\nROOT: "
        + str(ROOT)
        + "\n"
        + "=" * 70
    )
    print(banner, flush=True)

    # Tier 1 — imports (same spirit as CI “Lint (imports)”)
    print("\n[Tier 1a] Import smoke (evaluation + pipeline.config)", flush=True)
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from evaluation.evaluation_utils import EvaluationMetrics, check_answer_correctness  # noqa: F401
        from evaluation.config import PROJECT_ROOT  # noqa: F401
        from pipeline.config import HF_MODEL_NAME  # noqa: F401
        from pipeline.refine_loop import RefineLoop  # noqa: F401
        print("  OK: imports + RefineLoop symbol present", flush=True)
    except Exception as e:
        print("  FAIL:", e, flush=True)
        return 1

    # Tier 1 — no-model data smoke
    print("\n[Tier 1b] scripts/quick_smoke_test.py", flush=True)
    if _run([sys.executable, str(ROOT / "scripts" / "quick_smoke_test.py")]) != 0:
        return 1

    # Tier 1 — full tests (CI parity)
    print("\n[Tier 1c] pytest tests/ (PYTHONPATH=src, CI parity)", flush=True)
    env = {**os.environ, "PYTHONPATH": "src"}
    if _run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"], env=env) != 0:
        return 1

    # Tier 2 — Ralph gate CLI on fixture (simulates Tier-3 gate on saved eval JSON)
    print("\n[Tier 2] ralph_accuracy_gate.py on tests/fixtures/ralph_gate_pass.json", flush=True)
    fixture = ROOT / "tests" / "fixtures" / "ralph_gate_pass.json"
    if not fixture.is_file():
        print("  FAIL: missing", fixture, flush=True)
        return 1
    if _run([sys.executable, str(ROOT / "scripts" / "ralph_accuracy_gate.py"), str(fixture)]) != 0:
        return 1

    print("\n" + "=" * 70, flush=True)
    print("Ralph local verify: ALL PASS", flush=True)
    print("Next (Tier 3 / accuracy work): run a real eval, save results JSON, then:", flush=True)
    print(
        "  AIMO_OPTIMIZE_ACCURACY=1  # one knob among many; ablate one variable per experiment",
        flush=True,
    )
    print(
        "  python examples/run_numina_evaluation.py   # or Vertex path in docs/run-eval/RALPH_VERTEX.md",
        flush=True,
    )
    print("  python scripts/ralph_accuracy_gate.py results/<your>_results.json", flush=True)
    print("=" * 70, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
