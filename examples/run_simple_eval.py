"""
간단한 평가 실행 스크립트
최소한의 문제로 빠르게 평가를 실행합니다.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_EVAL_BALANCED_FILE
import json
import time

def simple_evaluate_with_mock(problems, max_problems=2):
    """Mock solver로 간단한 평가"""
    print("="*70)
    print("간단한 평가 실행 (Mock Solver)")
    print("="*70)
    print("\n참고: 실제 모델을 사용하려면 PipelineOrchestrator가 필요합니다.")
    print("현재는 Mock Solver로 평가 시스템을 테스트합니다.\n")
    
    if max_problems:
        problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name="Simple_Eval")
    metrics.start()
    
    for i, problem_data in enumerate(problems):
        problem = problem_data['problem']
        answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')
        
        print(f"\n[{i+1}/{len(problems)}] 문제:")
        print(f"  {problem[:150]}...")
        print(f"  정답: {answer}")
        
        # Mock solver (실제로는 orchestrator.solve_problem 호출)
        try:
            # 실제 모델 사용 시도
            try:
                from pipeline.orchestrator import PipelineOrchestrator
                print("  [INFO] PipelineOrchestrator 로딩 시도...")
                orchestrator = PipelineOrchestrator()
                print("  [SUCCESS] 모델 로드 성공!")
                
                start_time = time.time()
                result = orchestrator.solve_problem(
                    domain="general_math",
                    variables={},
                    problem_text=problem,
                    time_budget=10.0  # 빠른 테스트를 위해 10초로 단축
                )
                solve_time = time.time() - start_time
                
                predicted = result.get('answer', 'N/A')
                method = result.get('method', 'unknown')
                
            except Exception as e:
                print(f"  [WARN] 모델 로드 실패: {str(e)[:100]}")
                print("  [INFO] Mock solver 사용")
                # Fallback to mock
                import random
                solve_time = 0.1
                if random.random() < 0.5:
                    predicted = answer
                    method = 'mock_correct'
                else:
                    predicted = 'wrong_answer'
                    method = 'mock_wrong'
            
            print(f"  예측: {predicted}")
            print(f"  방법: {method}")
            
            is_correct = check_answer_correctness(answer, predicted)
            
            if is_correct:
                print(f"  [OK] 정답!")
            else:
                print(f"  [X] 오답")
            
            difficulty = determine_difficulty_from_source(source)
            
            eval_result = EvaluationResult(
                problem_id=i,
                problem=problem,
                reference_answer=answer,
                predicted_answer=predicted,
                is_correct=is_correct,
                solve_time=solve_time,
                method=method,
                difficulty=difficulty,
                source=source
            )
            
            metrics.add_result(eval_result)
            
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            eval_result = EvaluationResult(
                problem_id=i,
                problem=problem,
                reference_answer=answer,
                is_correct=False,
                error=str(e),
                difficulty=determine_difficulty_from_source(source),
                source=source
            )
            metrics.add_result(eval_result)
    
    metrics.finish()
    metrics.print_summary()
    
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename='simple_eval_results.json'
    )
    print(f"\n결과 저장: {output_path}")
    
    return metrics.calculate_metrics()

if __name__ == "__main__":
    print("데이터 로딩 중...")
    try:
        path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        print(f"로드 완료: {len(problems)}개 문제 ({path})")
    except Exception as e:
        print(f"오류: {e}")
        exit(1)
    
    print("\n평가 시작...")
    metrics = simple_evaluate_with_mock(problems, max_problems=2)
    
    print(f"\n{'='*70}")
    print(f"평가 완료! 정확도: {metrics['accuracy']:.2f}%")
    print(f"{'='*70}")
