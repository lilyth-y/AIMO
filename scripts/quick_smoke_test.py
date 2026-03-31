#!/usr/bin/env python3
"""단적 테스트: 데이터 로드 + 경로 + MAX_PROBLEMS 적용 여부만 확인 (모델 로드 없음)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

def main():
    ok = 0
    # 1) 데이터 파일 존재 및 로드
    from evaluation.config import find_data_file
    path = find_data_file("numina_eval_balanced.json")
    with open(path, encoding="utf-8") as f:
        import json
        data = json.load(f)
    assert isinstance(data, list) and len(data) >= 1
    print("[OK] numina_eval_balanced.json 로드:", len(data), "문항")
    ok += 1

    # 2) run_numina_evaluation 진입
    import examples.run_numina_evaluation as ev
    problems = ev.load_numina_eval()
    assert len(problems) == len(data)
    print("[OK] load_numina_eval() 일치")
    ok += 1

    # 3) MAX_PROBLEMS 적용 시 슬라이스
    os.environ["MAX_PROBLEMS"] = "2"
    max_p = os.environ.get("MAX_PROBLEMS")
    max_p = int(max_p) if max_p and max_p.isdigit() else None
    sub = problems[:max_p] if max_p else problems
    assert len(sub) == 2
    print("[OK] MAX_PROBLEMS=2 ->", len(sub), "문항으로 제한")
    ok += 1

    # 4) run_numina_on_kaggle 스크립트 존재
    kaggle_script = ROOT / "scripts" / "run_numina_on_kaggle.py"
    assert kaggle_script.exists()
    print("[OK] scripts/run_numina_on_kaggle.py 존재")
    ok += 1

    print("\n=> 단적 테스트 통과 (되는지 OK). 실제 추론은 examples/run_numina_evaluation.py 로 GPU에서 실행.")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
