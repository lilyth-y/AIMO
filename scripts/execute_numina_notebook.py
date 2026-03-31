#!/usr/bin/env python3
"""
CLI에서 Numina 평가 노트북(.ipynb)을 실행합니다.

사용 (프로젝트 루트에서):
  python scripts/execute_numina_notebook.py
  python scripts/execute_numina_notebook.py --notebook notebooks/run_numina_on_kaggle.ipynb
  python scripts/execute_numina_notebook.py --max-problems 5

nbconvert이 있으면 노트북을 실행하고, 없으면 examples/run_numina_evaluation.py를 직접 실행합니다.
노트북 내용이 /kaggle/working 경로를 쓰므로 Kaggle 외부에서는 실행이 실패할 수 있음. 그 경우 --script-only 로 평가만 실행.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def run_notebook_via_nbconvert(notebook_path: Path, output_path: Path, cwd: Path) -> int:
    """jupyter nbconvert --execute로 노트북 실행."""
    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor
    except ImportError:
        return -1
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)
    ep = ExecutePreprocessor(timeout=3600)
    ep.preprocess(nb, {"metadata": {"path": str(cwd)}})
    with open(output_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return 0


def main():
    root = project_root()
    parser = argparse.ArgumentParser(description="Run Numina evaluation notebook or script.")
    parser.add_argument(
        "--notebook",
        type=Path,
        default=root / "notebooks" / "run_numina_on_kaggle.ipynb",
        help="Path to .ipynb to execute",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output executed notebook path (default: same dir as notebook, suffix _executed)",
    )
    parser.add_argument(
        "--max-problems",
        type=str,
        default=os.environ.get("MAX_PROBLEMS", ""),
        help="MAX_PROBLEMS env (e.g. 5 for quick test)",
    )
    parser.add_argument(
        "--script-only",
        action="store_true",
        help="Do not run notebook; run examples/run_numina_evaluation.py only",
    )
    args = parser.parse_args()

    notebook_path = args.notebook if args.notebook.is_absolute() else root / args.notebook
    if not notebook_path.exists():
        print(f"[ERROR] Notebook not found: {notebook_path}", file=sys.stderr)
        return 1

    if args.max_problems:
        os.environ["MAX_PROBLEMS"] = args.max_problems

    if args.script_only:
        script = root / "examples" / "run_numina_evaluation.py"
        if not script.exists():
            print(f"[ERROR] Script not found: {script}", file=sys.stderr)
            return 1
        os.chdir(root)
        rc = subprocess.run([sys.executable, str(script)], env=os.environ)
        return rc.returncode

    # Try nbconvert-style execution (run all cells)
    out_path = args.output or (notebook_path.parent / f"{notebook_path.stem}_executed.ipynb")
    cwd = root
    print(f"[Run] Executing notebook: {notebook_path}")
    print(f"[Run] CWD: {cwd}")
    rc = run_notebook_via_nbconvert(notebook_path, out_path, cwd)
    if rc == 0:
        print(f"[OK] Executed notebook saved: {out_path}")
        return 0
    # Fallback: run the evaluation script (same as notebook's subprocess)
    print("[Run] nbconvert/nbformat not available; running run_numina_evaluation.py instead.")
    if not os.environ.get("AIMO_RESULTS_DIR"):
        os.environ.setdefault("AIMO_RESULTS_DIR", str(root))
    script = root / "examples" / "run_numina_evaluation.py"
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    rc = subprocess.run([sys.executable, str(script)], env=os.environ, cwd=str(root))
    return rc.returncode


if __name__ == "__main__":
    sys.exit(main())
