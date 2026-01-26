"""
초고속 평가 테스트 - 타임아웃 최소화
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
import json
import time

def fast_test():
    """1개 문제, 5초 타임아웃으로 초고속 테스트"""
    print("="*70)
    print("초고속 평가 테스트 (1개 문제, 5초 타임아웃)")
    print("="*70)
    
    # Load 1 problem
    path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    problem_data = problems[0]
    problem = problem_data['problem']
    answer = problem_data.get('answer', '')
    
    print(f"\n문제: {problem[:80]}...")
    print(f"정답: {answer}")
    
    try:
        from pipeline.orchestrator import PipelineOrchestrator
        print("\n[INFO] 모델 로딩 중...")
        start_load = time.time()
        orchestrator = PipelineOrchestrator()
        load_time = time.time() - start_load
        print(f"[SUCCESS] 모델 로드 완료 ({load_time:.1f}초)")
        
        print("\n[INFO] 문제 해결 중 (최대 5초)...")
        start_solve = time.time()
        result = orchestrator.solve_problem(
            domain="general_math",
            variables={},
            problem_text=problem,
            time_budget=5.0  # 매우 짧은 타임아웃
        )
        solve_time = time.time() - start_solve
        
        predicted = result.get('answer', 'N/A')
        method = result.get('method', 'unknown')
        
        print(f"\n예측: {predicted}")
        print(f"방법: {method}")
        print(f"소요 시간: {solve_time:.1f}초")
        
        is_correct = check_answer_correctness(answer, predicted)
        
        print(f"\n{'='*70}")
        if is_correct:
            print("[SUCCESS] 정답!")
        else:
            print("[INFO] 오답 (빠른 테스트이므로 정상)")
        print(f"총 소요 시간: {load_time + solve_time:.1f}초")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)[:200]}")

if __name__ == "__main__":
    import os
    os.environ['AIMO_MODEL'] = 'Qwen/Qwen2-1.5B-Instruct'
    os.environ['AIMO_QUANTIZATION'] = '4bit'
    os.environ['HF_HOME'] = 'C:\\hf_cache'
    os.environ['TRANSFORMERS_CACHE'] = 'C:\\hf_cache'
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = ''
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    fast_test()
