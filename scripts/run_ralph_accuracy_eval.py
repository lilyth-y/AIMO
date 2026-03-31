#!/usr/bin/env python3
"""
Ralph 정확도 루프용 Numina 평가 래퍼.

- 기본: ``AIMO_OPTIMIZE_ACCURACY=1`` (투표·후보 수 설정은 settings 참고)
- ``MAX_PROBLEMS`` 로 문제 수 제한 (기본 10, 스모크는 3~5 권장)
- 종료 후 ``results/<stem>_results*.json`` 에 대해 ``ralph_accuracy_gate`` 실행 (``--no-gate`` 로 생략)

예:
  python scripts/run_ralph_accuracy_eval.py --max-problems 5
  python scripts/run_ralph_accuracy_eval.py --difficulty-at-most easy --max-problems 20
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _result_filename(stem: str, difficulty_cap: str | None) -> str:
    suffix = f"_max_{difficulty_cap}" if difficulty_cap else ""
    return f"{stem}_results{suffix}.json"


def main() -> int:
    p = argparse.ArgumentParser(description="Run Numina eval with Ralph accuracy defaults + optional gate")
    p.add_argument("--max-problems", type=int, default=10, help="MAX_PROBLEMS (default 10)")
    p.add_argument(
        "--difficulty-at-most",
        choices=("easy", "medium", "hard"),
        default=None,
        help="EVAL_DIFFICULTY_AT_MOST / --difficulty-at-most for run_numina_evaluation",
    )
    p.add_argument("--data-file", default=None, help="EVAL_DATA_FILE override")
    p.add_argument("--no-gate", action="store_true", help="Skip ralph_accuracy_gate at end")
    p.add_argument("--no-optimize-accuracy", action="store_true", help="Do not set AIMO_OPTIMIZE_ACCURACY=1")
    args, passthrough = p.parse_known_args()

    env = os.environ.copy()
    if not args.no_optimize_accuracy:
        env["AIMO_OPTIMIZE_ACCURACY"] = "1"
    env["MAX_PROBLEMS"] = str(args.max_problems)

    cmd = [sys.executable, str(ROOT / "examples" / "run_numina_evaluation.py")]
    if args.difficulty_at_most:
        cmd += ["--difficulty-at-most", args.difficulty_at_most]
    if args.data_file:
        cmd += ["--data-file", args.data_file]
    cmd += passthrough

    print("run_ralph_accuracy_eval:", " ".join(cmd))
    print("env: AIMO_OPTIMIZE_ACCURACY=", env.get("AIMO_OPTIMIZE_ACCURACY"), "MAX_PROBLEMS=", env.get("MAX_PROBLEMS"))

    r = subprocess.run(cmd, cwd=str(ROOT), env=env)
    if r.returncode != 0 or args.no_gate:
        return r.returncode

    # Resolve results path (same logic as examples/run_numina_evaluation.py main)
    sys.path.insert(0, str(ROOT / "src"))
    from evaluation.config import NUMINA_EVAL_BALANCED_FILE, find_data_file  # noqa: E402

    data_file = args.data_file or os.environ.get("EVAL_DATA_FILE", "").strip() or NUMINA_EVAL_BALANCED_FILE
    path_resolved = find_data_file(data_file)
    stem = path_resolved.stem
    res_name = _result_filename(stem, args.difficulty_at_most)
    json_path = ROOT / "results" / res_name
    if not json_path.is_file():
        print(f"[gate] skip: results file not found: {json_path}", file=sys.stderr)
        return r.returncode

    gate = ROOT / "scripts" / "ralph_accuracy_gate.py"
    print("\n--- ralph_accuracy_gate ---")
    g = subprocess.run([sys.executable, str(gate), str(json_path)], cwd=str(ROOT), env=env)
    return g.returncode


if __name__ == "__main__":
    raise SystemExit(main())
