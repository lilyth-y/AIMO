"""
Delegate to `examples/run_numina_evaluation.py` so Docker `entrypoint.sh` `eval` mode works from repo root.
"""
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, "examples", "run_numina_evaluation.py")

if not os.path.isfile(TARGET):
    print(f"Missing: {TARGET}", file=sys.stderr)
    sys.exit(1)

os.chdir(ROOT)
runpy.run_path(TARGET, run_name="__main__")
