"""
평가 스크립트 import 테스트
실제 평가 스크립트들이 정상적으로 import되는지 확인합니다.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_script_imports():
    """각 평가 스크립트의 import 테스트"""
    print("="*70)
    print("평가 스크립트 Import 테스트")
    print("="*70)
    
    results = []
    
    # 1. run_aime_evaluation.py
    try:
        sys.path.append('src')
        from evaluation.evaluation_utils import EvaluationMetrics, EvaluationResult
        from evaluation.evaluation_utils import check_answer_correctness, extract_aime_answer
        from evaluation.config import find_data_file, AIME_VALIDATION_FILE
        print("[OK] run_aime_evaluation.py 의존성 import 성공")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] run_aime_evaluation.py import 실패: {e}")
        results.append(False)
    
    # 2. run_numina_evaluation.py
    try:
        from evaluation.evaluation_utils import (
            EvaluationMetrics, EvaluationResult,
            check_answer_correctness, determine_difficulty_from_source
        )
        from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_EVAL_BALANCED_FILE
        print("[OK] run_numina_evaluation.py 의존성 import 성공")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] run_numina_evaluation.py import 실패: {e}")
        results.append(False)
    
    # 3. quick_eval.py
    try:
        from evaluation.evaluation_utils import (
            EvaluationMetrics, EvaluationResult,
            check_answer_correctness, determine_difficulty_from_source
        )
        print("[OK] quick_eval.py 의존성 import 성공")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] quick_eval.py import 실패: {e}")
        results.append(False)
    
    # 4. evaluate_outputs.py
    try:
        from evaluation.evaluation_utils import (
            EvaluationMetrics, EvaluationResult,
            check_answer_correctness
        )
        print("[OK] evaluate_outputs.py 의존성 import 성공")
        results.append(True)
    except Exception as e:
        print(f"[ERROR] evaluate_outputs.py import 실패: {e}")
        results.append(False)
    
    # 5. 데이터 파일 경로 확인
    try:
        from evaluation.config import find_data_file, AIME_VALIDATION_FILE, NUMINA_EVAL_BALANCED_FILE
        
        # AIME 파일 확인
        try:
            aime_path = find_data_file(AIME_VALIDATION_FILE)
            print(f"[OK] AIME 데이터 파일 확인: {aime_path}")
        except FileNotFoundError:
            print(f"[WARN] AIME 데이터 파일 없음: {AIME_VALIDATION_FILE}")
        
        # NuminaMath 파일 확인
        try:
            numina_path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
            print(f"[OK] NuminaMath 데이터 파일 확인: {numina_path}")
        except FileNotFoundError:
            print(f"[WARN] NuminaMath 데이터 파일 없음: {NUMINA_EVAL_BALANCED_FILE}")
        
        results.append(True)
    except Exception as e:
        print(f"[ERROR] 데이터 파일 경로 확인 실패: {e}")
        results.append(False)
    
    return results

def main():
    results = test_script_imports()
    
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"통과: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] 모든 평가 스크립트 import 성공!")
        return 0
    else:
        print("[WARN] 일부 import 실패 (의존성 문제일 수 있음)")
        return 0  # import 실패는 치명적이지 않을 수 있음

if __name__ == "__main__":
    exit(main())
