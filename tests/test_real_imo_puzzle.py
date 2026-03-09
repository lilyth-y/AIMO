"""
실제 데이터셋에서 IMO 급 문제와 퍼즐 문제 찾아서 테스트
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
from src.pipeline.feature_extractor import rapid_intuition_phase

def find_test_problems():
    """실제 데이터셋에서 IMO 급 문제와 퍼즐 문제 찾기"""
    print("=" * 70)
    print("실제 데이터셋에서 테스트 문제 찾기")
    print("=" * 70)
    
    path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        problems = json.load(f)
    
    # IMO 급 문제 찾기 (olympiads 소스)
    imo_problems = []
    puzzle_problems = []
    
    for prob in problems:
        source = prob.get('source', '')
        problem_text = prob.get('problem', '')
        
        # IMO 급 문제 (olympiads, olympiads_ref)
        if source in ['olympiads', 'olympiads_ref', 'amc_aime']:
            if len(imo_problems) < 2:
                imo_problems.append(prob)
        
        # 퍼즐 문제 (키워드 기반)
        problem_lower = problem_text.lower()
        if any(kw in problem_lower for kw in ['puzzle', '퍼즐', 'constraint', '제약', 'logic', '논리']):
            if len(puzzle_problems) < 2:
                puzzle_problems.append(prob)
    
    print(f"\n찾은 IMO 급 문제: {len(imo_problems)}개")
    print(f"찾은 퍼즐 문제: {len(puzzle_problems)}개")
    
    # 문제 분류 확인
    print("\n" + "=" * 70)
    print("문제 분류 확인")
    print("=" * 70)
    
    all_test_problems = imo_problems + puzzle_problems
    
    for i, prob in enumerate(all_test_problems):
        problem_text = prob.get('problem', '')
        answer = prob.get('answer', 'N/A')
        source = prob.get('source', 'unknown')
        
        problem_type, strategy = rapid_intuition_phase(problem_text)
        
        print(f"\n[{i+1}] 소스: {source}")
        print(f"  분류: {problem_type}")
        print(f"  전략: {strategy}")
        print(f"  문제: {problem_text[:100]}...")
        print(f"  정답: {answer}")
    
    return all_test_problems

def test_solve_real_problems(problems, max_problems=2):
    """실제 문제 해결 테스트"""
    print("\n" + "=" * 70)
    print("실제 문제 해결 테스트")
    print("=" * 70)
    
    import os
    os.environ['MATHCODEORCHESTRATOR_MODEL'] = 'Qwen/Qwen2-1.5B-Instruct'
    os.environ['MATHCODEORCHESTRATOR_QUANTIZATION'] = '4bit'
    os.environ['HF_HOME'] = 'C:\\hf_cache'
    os.environ['TRANSFORMERS_CACHE'] = 'C:\\hf_cache'
    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = ''
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    if not problems:
        print("테스트할 문제가 없습니다.")
        return
    
    # 최대 2개만 테스트 (빠른 확인)
    test_problems = problems[:max_problems]
    
    try:
        from src.pipeline.orchestrator import PipelineOrchestrator
        print("\n[INFO] Orchestrator 초기화 중...")
        orchestrator = PipelineOrchestrator()
        print("[SUCCESS] 초기화 완료!\n")
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        print("\n프롬프트 생성만 테스트합니다...")
        test_prompt_generation(test_problems)
        return
    
    from evaluation.evaluation_utils import (
        EvaluationMetrics, EvaluationResult,
        check_answer_correctness, determine_difficulty_from_source
    )
    
    metrics = EvaluationMetrics(dataset_name="Real_IMO_Puzzle_Test")
    metrics.start()
    
    for i, prob in enumerate(test_problems):
        problem_text = prob.get('problem', '')
        answer = prob.get('answer', 'N/A')
        source = prob.get('source', 'unknown')
        
        print(f"\n{'='*70}")
        print(f"[{i+1}/{len(test_problems)}] 소스: {source}")
        print(f"{'='*70}")
        print(f"문제: {problem_text[:150]}...")
        print(f"정답: {answer}")
        
        try:
            import time
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem_text,
                time_budget=20.0  # 빠른 테스트
            )
            solve_time = time.time() - start_time
            
            predicted = result.get('answer', 'N/A')
            method = result.get('method', 'unknown')
            
            print(f"\n결과:")
            print(f"  예측 답: {predicted}")
            print(f"  방법: {method}")
            print(f"  소요 시간: {solve_time:.2f}초")
            
            is_correct = check_answer_correctness(answer, predicted)
            
            if is_correct:
                print(f"  상태: [OK] 정답!")
            else:
                print(f"  상태: [X] 오답")
            
            eval_result = EvaluationResult(
                problem_id=i,
                problem=problem_text,
                reference_answer=answer,
                predicted_answer=predicted,
                is_correct=is_correct,
                solve_time=solve_time,
                method=method,
                difficulty=determine_difficulty_from_source(source),
                source=source
            )
            metrics.add_result(eval_result)
            
        except Exception as e:
            print(f"\n[ERROR] 오류: {e}")
            eval_result = EvaluationResult(
                problem_id=i,
                problem=problem_text,
                reference_answer=answer,
                is_correct=False,
                error=str(e),
                difficulty=determine_difficulty_from_source(source),
                source=source
            )
            metrics.add_result(eval_result)
    
    metrics.finish()
    metrics.print_summary()
    
    from evaluation.config import ensure_dir, RESULTS_DIR
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename='real_imo_puzzle_test_results.json'
    )
    print(f"\n결과 저장: {output_path}")

def test_prompt_generation(problems):
    """프롬프트 생성만 테스트 (모델 로딩 없이)"""
    from src.pipeline.solver import Solver
    
    solver = Solver.__new__(Solver)  # 인스턴스 생성 없이 메서드만 테스트
    
    for i, prob in enumerate(problems):
        problem_text = prob.get('problem', '')
        source = prob.get('source', 'unknown')
        
        print(f"\n[{i+1}] 소스: {source}")
        print(f"문제: {problem_text[:100]}...")
        
        # Simulator 전략으로 프롬프트 생성
        prompt = solver._construct_prompt(
            problem_text=problem_text,
            strategy="Path A: The Simulator",
            reasoning_text=None,
            lemma_snippets=None
        )
        
        print(f"\n생성된 프롬프트:")
        print("-" * 70)
        print(prompt[:300] + "..." if len(prompt) > 300 else prompt)
        print("-" * 70)
        
        # 퍼즐 키워드 확인
        is_puzzle = any(kw in problem_text.lower() for kw in ['puzzle', '퍼즐', 'constraint', '제약', 'logic', '논리'])
        has_constraint = 'constraint' in prompt.lower()
        
        if is_puzzle and has_constraint:
            print("✓ 퍼즐 문제가 제대로 감지되고 전용 프롬프트가 생성되었습니다!")
        elif is_puzzle:
            print("⚠ 퍼즐 문제인데 전용 프롬프트가 생성되지 않았습니다.")
        else:
            print("ℹ 일반 문제입니다.")

if __name__ == "__main__":
    # 1. 실제 데이터셋에서 문제 찾기
    problems = find_test_problems()
    
    # 2. 실제 해결 테스트
    if problems:
        print("\n" + "=" * 70)
        print("실제 해결 테스트를 시작합니다...")
        print("=" * 70)
        test_solve_real_problems(problems, max_problems=2)
    else:
        print("\n테스트할 문제를 찾지 못했습니다.")
