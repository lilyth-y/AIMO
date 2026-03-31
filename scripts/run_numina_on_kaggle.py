#!/usr/bin/env python3
"""
Kaggle에서 Numina 평가를 돌리기 위한 진입 스크립트.

- Kaggle 환경(/kaggle/working 등)이 있으면 데이터·결과 경로를 자동 설정.
- 그 다음 examples/run_numina_evaluation.py 를 실행합니다.

사용 (Kaggle 노트북에서):
  !python scripts/run_numina_on_kaggle.py

또는 환경 변수만 설정하고 직접 실행:
  !python examples/run_numina_evaluation.py
"""

import os
import sys
import subprocess
from pathlib import Path

def _project_root():
    root = Path(__file__).resolve().parent.parent
    return root

def _is_kaggle():
    return Path("/kaggle/working").exists() or os.environ.get("KAGGLE_KERNEL_RUN_TYPE")

def main():
    root = _project_root()
    os.chdir(root)

    if _is_kaggle():
        # 결과를 /kaggle/working/results 에 저장
        os.environ.setdefault("AIMO_RESULTS_DIR", "/kaggle/working")
        # 데이터: 리포 data/ 우선, 없으면 /kaggle/working/data, /kaggle/input
        if not os.environ.get("AIMO_DATA_DIR") and not os.environ.get("KAGGLE_DATA_DIR"):
            repo_data = root / "data"
            if (repo_data / "numina_eval_balanced.json").exists():
                os.environ.setdefault("AIMO_DATA_DIR", str(repo_data))
            else:
                for d in ["/kaggle/working/data", "/kaggle/input"]:
                    if Path(d).exists():
                        os.environ.setdefault("AIMO_DATA_DIR", d)
                        break
        # 문항 하나에서 멈추지 않도록 기본 15분 타임아웃 (선택)
        os.environ.setdefault("EVAL_PROBLEM_TIMEOUT", "900")
        print("[Kaggle] AIMO_RESULTS_DIR=%s" % os.environ.get("AIMO_RESULTS_DIR"))
        print("[Kaggle] AIMO_DATA_DIR=%s" % os.environ.get("AIMO_DATA_DIR", "(not set)"))
        print("[Kaggle] EVAL_PROBLEM_TIMEOUT=%s" % os.environ.get("EVAL_PROBLEM_TIMEOUT"))

    script = root / "examples" / "run_numina_evaluation.py"
    if not script.exists():
        print("ERROR: %s not found" % script)
        sys.exit(1)
    rc = subprocess.run([sys.executable, str(script)], cwd=str(root))
    sys.exit(rc.returncode)

if __name__ == "__main__":
    main()
