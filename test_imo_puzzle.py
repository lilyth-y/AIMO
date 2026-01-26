"""
IMO 급 문제와 수학 퍼즐 문제 해결 테스트
실제 문제를 풀어서 시스템이 제대로 작동하는지 확인
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
from src.pipeline.feature_extractor import rapid_intuition_phase

# IMO 급 문제 예시 (실제 평가 데이터에서 찾거나 직접 작성)
IMO_PROBLEMS = [
    {
        "name": "IMO 스타일 조합론 문제",
        "problem": "Find the number of ways to arrange 5 distinct objects in a row such that no two adjacent objects have the same property. Given that 2 objects are of type A and 3 objects are of type B.",
        "answer": "12",
        "type": "combinatorics",
        "difficulty": "IMO"
    },
    {
        "name": "수학 퍼즐 - 제약 조건",
        "problem": "A puzzle: Find three positive integers a, b, c such that a + b + c = 12, a * b * c is maximum, and a < b < c. What is the product a * b * c?",
        "answer": "40",
        "type": "puzzle",
        "difficulty": "medium"
    },
    {
        "name": "수학 퍼즐 - 논리 추론",
        "problem": "A logic puzzle: Three numbers satisfy: x + y = 10, y + z = 15, x + z = 13. What is x * y * z?",
        "answer": "144",
        "type": "puzzle",
        "difficulty": "medium"
    }
]

def test_problem_classification():
    """문제 분류 테스트"""
    print("=" * 70)
    print("문제 분류 테스트")
    print("=" * 70)
    
    for prob in IMO_PROBLEMS:
        problem_type, strategy = rapid_intuition_phase(prob["problem"])
        print(f"\n문제: {prob['name']}")
        print(f"  타입: {problem_type}")
        print(f"  전략: {strategy}")
        print(f"  난이도: {prob['difficulty']}")
        print(f"  예상 답: {prob['answer']}")

def test_solve_problems():
    """실제 문제 해결 테스트"""
    print("\n" + "=" * 70)
    print("실제 문제 해결 테스트")
    print("=" * 70)
    
    import os
    os.environ['AIMO_MODEL'] = 'Qwen/Qwen2-1.5B-Instruct'
    os.environ['AIMO_QUANTIZATION'] = '4bit'
    os.environ['HF_HOME'] = 'C:\\hf_cache'
    os.environ['TRANSFORMERS_CACHE'] = 'C:\\hf_cache'
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = ''
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        from src.pipeline.orchestrator import PipelineOrchestrator
        print("\n[INFO] Orchestrator 초기화 중...")
        orchestrator = PipelineOrchestrator()
        print("[SUCCESS] 초기화 완료!\n")
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        print("Mock 모드로 진행합니다...")
        return
    
    metrics = EvaluationMetrics(dataset_name="IMO_Puzzle_Test")
    metrics.start()
    
    for i, prob in enumerate(IMO_PROBLEMS):
        print(f"\n{'='*70}")
        print(f"[{i+1}/{len(IMO_PROBLEMS)}] {prob['name']}")
        print(f"{'='*70}")
        print(f"문제: {prob['problem']}")
        print(f"예상 답: {prob['answer']}")
        print(f"난이도: {prob['difficulty']}")
        
        try:
            import time
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=prob['problem'],
                time_budget=30.0
            )
            solve_time = time.time() - start_time
            
            predicted = result.get('answer', 'N/A')
            method = result.get('method', 'unknown')
            
            print(f"\n결과:")
            print(f"  예측 답: {predicted}")
            print(f"  방법: {method}")
            print(f"  소요 시간: {solve_time:.2f}초")
            
            is_correct = check_answer_correctness(prob['answer'], predicted)
            
            if is_correct:
                print(f"  상태: [OK] 정답!")
            else:
                print(f"  상태: [X] 오답 (예상: {prob['answer']}, 예측: {predicted})")
            
            eval_result = EvaluationResult(
                problem_id=i,
                problem=prob['problem'],
                reference_answer=prob['answer'],
                predicted_answer=predicted,
                is_correct=is_correct,
                solve_time=solve_time,
                method=method,
                difficulty=prob['difficulty'],
                source='test',
                metadata={'name': prob['name'], 'type': prob['type']}
            )
            metrics.add_result(eval_result)
            
        except Exception as e:
            print(f"\n[ERROR] 오류 발생: {e}")
            eval_result = EvaluationResult(
                problem_id=i,
                problem=prob['problem'],
                reference_answer=prob['answer'],
                is_correct=False,
                error=str(e),
                difficulty=prob['difficulty'],
                source='test',
                metadata={'name': prob['name'], 'type': prob['type']}
            )
            metrics.add_result(eval_result)
    
    metrics.finish()
    metrics.print_summary()
    
    # 결과 저장
    from evaluation.config import ensure_dir, RESULTS_DIR
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename='imo_puzzle_test_results.json'
    )
    print(f"\n결과 저장: {output_path}")

if __name__ == "__main__":
    # 1. 분류 테스트
    test_problem_classification()
    
    # 2. 해결 테스트
    print("\n" + "=" * 70)
    print("실제 해결 테스트를 시작합니다...")
    print("=" * 70)
    test_solve_problems()
