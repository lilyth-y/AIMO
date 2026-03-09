"""
Mock 평가 테스트
실제 모델 없이 평가 시스템이 잘 작동하는지 확인합니다.
"""

import sys
import os
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_EVAL_BALANCED_FILE

def mock_solve_problem(problem_text, answer):
    """Mock solver - 실제 답변을 반환하거나 랜덤하게 오답 반환"""
    import random
    # 70% 확률로 정답 반환 (테스트용)
    if random.random() < 0.7:
        return {
            'answer': answer,
            'method': 'mock_solver'
        }
    else:
        return {
            'answer': str(int(answer) + 1) if answer.isdigit() else 'wrong',
            'method': 'mock_solver'
        }

def evaluate_mock(problems, max_problems=5):
    """
    Mock 평가 실행
    """
    if max_problems:
        problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name="Mock_Evaluation")
    metrics.start()
    
    print(f"\n{'='*70}")
    print(f"Mock Evaluation: {len(problems)} problems")
    print(f"{'='*70}\n")
    
    for i, problem_data in enumerate(problems):
        problem = problem_data['problem']
        answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')
        
        print(f"\n[{i+1}/{len(problems)}] Problem: {problem[:80]}...")
        print(f"Expected: {answer}")
        
        try:
            # Mock solve
            start_time = time.time()
            result = mock_solve_problem(problem, answer)
            solve_time = time.time() - start_time
            
            predicted = result.get('answer', 'N/A')
            method = result.get('method', 'unknown')
            
            print(f"Predicted: {predicted}")
            print(f"Method: {method}")
            
            # Check correctness using unified utility
            is_correct = check_answer_correctness(answer, predicted)
            
            if is_correct:
                print("[OK] CORRECT")
            else:
                print("[X] WRONG")
            
            # Determine difficulty
            difficulty = determine_difficulty_from_source(source)
            
            # Create result entry
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
            print(f"[ERROR] {str(e)}")
            difficulty = determine_difficulty_from_source(source)
            eval_result = EvaluationResult(
                problem_id=i,
                problem=problem,
                reference_answer=answer,
                is_correct=False,
                error=str(e),
                difficulty=difficulty,
                source=source
            )
            metrics.add_result(eval_result)
    
    metrics.finish()
    
    # Print summary
    metrics.print_summary()
    
    # Save results
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename='mock_evaluation_results.json'
    )
    print(f"Results saved to: {output_path}")
    
    final_metrics = metrics.calculate_metrics()
    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

def main():
    print("="*70)
    print("Mock Evaluation Test")
    print("="*70)
    
    # Load problems
    print("\nLoading problems...")
    try:
        path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            problems = json.load(f)
        print(f"Loaded {len(problems)} problems from: {path}")
    except FileNotFoundError:
        print(f"[ERROR] 데이터 파일을 찾을 수 없습니다: {NUMINA_EVAL_BALANCED_FILE}")
        return 1
    
    # Run mock evaluation
    print("\nRunning mock evaluation...")
    accuracy, results = evaluate_mock(problems, max_problems=5)
    
    print(f"\n{'='*70}")
    print(f"[SUCCESS] Mock evaluation completed!")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"{'='*70}")
    
    return 0

if __name__ == "__main__":
    exit(main())
