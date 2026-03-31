"""
빠른 평가 테스트 - 1개 문제만
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_EVAL_BALANCED_FILE
import json
import time

def quick_test():
    """1개 문제로 빠르게 테스트"""
    print("="*70)
    print("빠른 평가 테스트 (1개 문제)")
    print("="*70)
    
    # Load problems
    path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    # Take only 1 problem
    problem_data = problems[0]
    problem = problem_data['problem']
    answer = problem_data.get('answer', '')
    source = problem_data.get('source', 'unknown')
    
    print(f"\n문제: {problem[:100]}...")
    print(f"정답: {answer}")
    
    # Try to use actual orchestrator
    try:
        from pipeline.orchestrator import PipelineOrchestrator
        print("\n[INFO] PipelineOrchestrator 로딩 시도...")
        orchestrator = PipelineOrchestrator()
        print("[SUCCESS] 모델 로드 성공!")
        
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
        
        print(f"\n예측: {predicted}")
        print(f"방법: {method}")
        print(f"소요 시간: {solve_time:.2f}초")
        
        is_correct = check_answer_correctness(answer, predicted)
        
        if is_correct:
            print("\n[OK] 정답!")
        else:
            print("\n[X] 오답")
        
        print(f"\n{'='*70}")
        print(f"테스트 완료! 정확도: {'100%' if is_correct else '0%'}")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    os.environ['MATHCODEORCHESTRATOR_MODEL'] = 'Qwen/Qwen2-1.5B-Instruct'
    os.environ['OMI_QUANTIZATION'] = '4bit'
    os.environ['HF_HOME'] = 'C:\\hf_cache'
    os.environ['TRANSFORMERS_CACHE'] = 'C:\\hf_cache'
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = ''
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    quick_test()
