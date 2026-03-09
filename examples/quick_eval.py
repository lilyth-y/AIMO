"""
Quick evaluation with minimal memory footprint
Loads model once and keeps it in memory for multiple problems
"""

import sys
import os
import json

# Reduce TensorFlow oneDNN log noise (set before any tf import)
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

# 테스트용: Quick Eval에서는 기본으로 작은 모델 사용 (빠름). 큰 모델 쓰려면 OMI_MODEL 설정.
if "OMI_MODEL" not in os.environ and "AIMO_MODEL" not in os.environ:
    os.environ["OMI_MODEL"] = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

# Add project root and src to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Now import
from pipeline.orchestrator import PipelineOrchestrator
from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from tqdm import tqdm

def load_numina_eval():
    """Load NuminaMath balanced evaluation set"""
    from evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
    path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        print(f"Loaded NuminaMath eval from: {path}")
        return json.load(f)

def evaluate_quick(orchestrator, problems, max_problems=5):
    """
    Lightweight evaluation using unified evaluation utilities
    """
    # Limit problems
    problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name="Quick_Eval")
    metrics.start()
    
    print(f"\n{'='*70}")
    print(f"Quick Evaluation: {len(problems)} problems")
    print(f"{'='*70}\n")
    
    for i, problem_data in enumerate(tqdm(problems, desc="Solving")):
        problem = problem_data['problem']
        answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')
        
        print(f"\n[{i+1}/{len(problems)}] Problem: {problem[:100]}...")
        print(f"Expected: {answer}")
        
        try:
            # Solve
            import time
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem,
                time_budget=60.0
            )
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

            # P5: capture failure reason for error_summary
            fail_reason = None
            if not is_correct or result.get('method') == 'all_failed':
                ex = result.get('execution_result') or result.get('error')
                if ex and isinstance(ex, str) and ('Error:' in ex or 'failed' in ex.lower()):
                    fail_reason = ex[:500]

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
                source=source,
                error=fail_reason
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
    output_path = metrics.save_results(
        output_dir='results',
        filename='quick_eval_results.json'
    )
    print(f"Results saved to: {output_path}")

    final_metrics = metrics.calculate_metrics()
    try:
        from evaluation.run_helpers import save_gradient_and_error_summary, print_gradient_summary
        grad_path = save_gradient_and_error_summary(
            final_metrics,
            [r.to_dict() for r in metrics.results],
            output_dir=os.path.join(project_root, 'results'),
            dataset_name='Quick_Eval',
            filename='gradient_report_quick_eval.json'
        )
        print(f"Gradient report saved to: {grad_path}")
        print_gradient_summary(final_metrics)
    except Exception as e:
        print(f"[Gradient report skip] {e}")

    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

if __name__ == "__main__":
    # AIMO_FAST_EVAL=1 이면 1문항만, 빠른 평가용 (CPU 오프로드 시 느리므로)
    fast_eval = os.environ.get("AIMO_FAST_EVAL", "0") == "1"
    max_problems = int(os.environ.get("MAX_PROBLEMS", "1" if fast_eval else "5"))
    if fast_eval:
        print("[Fast Eval] 1 problem. For faster runs: OMI_MODEL=Qwen/Qwen2.5-Coder-1.5B-Instruct or set AIMO_MAX_NEW_TOKENS=256")
    print("Loading problems...")
    problems = load_numina_eval()
    print(f"Loaded {len(problems)} problems")
    
    print("\nInitializing solver...")
    print(f"Model: {os.environ.get('OMI_MODEL', os.environ.get('AIMO_MODEL', 'default'))}")
    orchestrator = PipelineOrchestrator()
    print("Solver ready!")
    
    # Run quick eval (MAX_PROBLEMS env overrides default 5)
    accuracy, results = evaluate_quick(orchestrator, problems, max_problems=max_problems)
    
    print(f"\n[OK] Evaluation completed. Accuracy: {accuracy:.2f}%")
