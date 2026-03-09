"""
평가 유틸리티 테스트 스크립트
import 및 기본 기능이 잘 작동하는지 확인합니다.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def test_imports():
    """모든 import가 정상적으로 작동하는지 테스트"""
    print("="*70)
    print("1. Import 테스트")
    print("="*70)
    
    try:
        from evaluation.evaluation_utils import (
            EvaluationResult,
            EvaluationMetrics,
            check_answer_correctness,
            extract_aime_answer,
            determine_difficulty_from_source
        )
        print("[OK] evaluation_utils import 성공")
        
        from evaluation.config import (
            find_data_file,
            ensure_dir,
            RESULTS_DIR,
            AIME_VALIDATION_FILE,
            NUMINA_EVAL_BALANCED_FILE
        )
        print("[OK] config import 성공")
        
        from evaluation import (
            EvaluationResult,
            EvaluationMetrics,
            check_answer_correctness
        )
        print("[OK] evaluation 모듈 import 성공")
        
        return True
    except Exception as e:
        print(f"[ERROR] Import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_evaluation_result():
    """EvaluationResult 클래스 테스트"""
    print("\n" + "="*70)
    print("2. EvaluationResult 클래스 테스트")
    print("="*70)
    
    try:
        from evaluation.evaluation_utils import EvaluationResult
        
        # 기본 결과 생성
        result = EvaluationResult(
            problem_id=1,
            problem="테스트 문제",
            reference_answer="42",
            predicted_answer="42",
            is_correct=True,
            solve_time=1.5,
            method="test_method"
        )
        
        # to_dict() 테스트
        result_dict = result.to_dict()
        assert result_dict['problem_id'] == 1
        assert result_dict['is_correct'] == True
        assert result_dict['reference_answer'] == "42"
        print("[OK] EvaluationResult 생성 및 to_dict() 성공")
        
        return True
    except Exception as e:
        print(f"[ERROR] EvaluationResult 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_evaluation_metrics():
    """EvaluationMetrics 클래스 테스트"""
    print("\n" + "="*70)
    print("3. EvaluationMetrics 클래스 테스트")
    print("="*70)
    
    try:
        from evaluation.evaluation_utils import EvaluationMetrics, EvaluationResult
        
        metrics = EvaluationMetrics(dataset_name="Test_Dataset")
        metrics.start()
        
        # 테스트 결과 추가
        for i in range(5):
            result = EvaluationResult(
                problem_id=i,
                problem=f"문제 {i}",
                reference_answer="10",
                predicted_answer="10" if i < 3 else "20",  # 처음 3개만 정답
                is_correct=(i < 3),
                solve_time=1.0 + i * 0.1,
                method="test"
            )
            metrics.add_result(result)
        
        metrics.finish()
        
        # 메트릭 계산
        calculated_metrics = metrics.calculate_metrics()
        
        assert calculated_metrics['total'] == 5
        assert calculated_metrics['correct'] == 3
        assert calculated_metrics['accuracy'] == 60.0
        print(f"[OK] 메트릭 계산 성공: {calculated_metrics['accuracy']:.1f}%")
        
        # 요약 출력 테스트
        print("\n요약 출력:")
        metrics.print_summary()
        
        return True
    except Exception as e:
        print(f"[ERROR] EvaluationMetrics 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_answer_correctness():
    """답변 정확도 검사 함수 테스트"""
    print("\n" + "="*70)
    print("4. 답변 정확도 검사 테스트")
    print("="*70)
    
    try:
        from evaluation.evaluation_utils import check_answer_correctness
        
        # 정확히 일치하는 경우
        assert check_answer_correctness("42", "42") == True
        print("[OK] 정확한 일치 검사 성공")
        
        # 공백 차이
        assert check_answer_correctness(" 42 ", "42") == True
        print("[OK] 공백 정규화 검사 성공")
        
        # None 처리
        assert check_answer_correctness("42", None) == False
        assert check_answer_correctness(None, "42") == False
        print("[OK] None 처리 검사 성공")
        
        # N/A 처리
        assert check_answer_correctness("42", "N/A") == False
        print("[OK] N/A 처리 검사 성공")
        
        return True
    except Exception as e:
        print(f"[ERROR] 답변 정확도 검사 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_paths():
    """설정 파일 경로 테스트"""
    print("\n" + "="*70)
    print("5. 설정 파일 경로 테스트")
    print("="*70)
    
    try:
        from evaluation.config import (
            find_data_file,
            ensure_dir,
            RESULTS_DIR,
            AIME_VALIDATION_FILE,
            NUMINA_EVAL_BALANCED_FILE
        )
        
        # 결과 디렉터리 생성 테스트
        ensure_dir(RESULTS_DIR)
        print(f"[OK] 결과 디렉터리 확인: {RESULTS_DIR}")
        
        # 데이터 파일 찾기 테스트 (파일이 없어도 에러 메시지 확인)
        try:
            path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
            print(f"[OK] NuminaMath 데이터 파일 찾기 성공: {path}")
        except FileNotFoundError as e:
            print(f"[WARN] NuminaMath 데이터 파일 없음 (예상 가능): {NUMINA_EVAL_BALANCED_FILE}")
        
        try:
            path = find_data_file(AIME_VALIDATION_FILE)
            print(f"[OK] AIME 데이터 파일 찾기 성공: {path}")
        except FileNotFoundError as e:
            print(f"[WARN] AIME 데이터 파일 없음 (예상 가능): {AIME_VALIDATION_FILE}")
        
        return True
    except Exception as e:
        print(f"[ERROR] 설정 파일 경로 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_utility_functions():
    """유틸리티 함수 테스트"""
    print("\n" + "="*70)
    print("6. 유틸리티 함수 테스트")
    print("="*70)
    
    try:
        from evaluation.evaluation_utils import (
            extract_aime_answer,
            determine_difficulty_from_source
        )
        
        # AIME 답변 추출 테스트
        solution_text = "The answer is \\boxed{42}."
        answer = extract_aime_answer(solution_text)
        assert answer == "42"
        print("[OK] AIME 답변 추출 성공")
        
        # 난이도 결정 테스트
        assert determine_difficulty_from_source("orca_math") == "easy"
        assert determine_difficulty_from_source("amc_aime") == "hard"
        assert determine_difficulty_from_source("unknown") == "medium"
        print("[OK] 난이도 결정 성공")
        
        return True
    except Exception as e:
        print(f"[ERROR] 유틸리티 함수 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """모든 테스트 실행"""
    print("\n" + "="*70)
    print("평가 유틸리티 테스트 시작")
    print("="*70)
    
    tests = [
        test_imports,
        test_evaluation_result,
        test_evaluation_metrics,
        test_answer_correctness,
        test_config_paths,
        test_utility_functions
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] 테스트 실행 중 오류: {e}")
            results.append(False)
    
    # 최종 결과
    print("\n" + "="*70)
    print("테스트 결과 요약")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"통과: {passed}/{total}")
    
    if passed == total:
        print("[SUCCESS] 모든 테스트 통과!")
        return 0
    else:
        print("[ERROR] 일부 테스트 실패")
        return 1

if __name__ == "__main__":
    exit(main())
