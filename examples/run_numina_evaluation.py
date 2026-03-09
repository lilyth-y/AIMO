"""
Run evaluation on NuminaMath Balanced Set (60 problems)
- Mixed difficulty: 10 easy, 20 medium, 30 hard
- Development/testing benchmark
"""

import sys
import os
# Reduce TensorFlow oneDNN log noise (set before any tf import)
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

import json
import time
from pipeline.orchestrator import PipelineOrchestrator
from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from tqdm import tqdm

from evaluation.config import find_data_file, ensure_dir, RESULTS_DIR, NUMINA_EVAL_BALANCED_FILE

def load_numina_eval():
    """Load NuminaMath balanced evaluation set (path-safe from any CWD)"""
    path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        print(f"Loaded NuminaMath eval from: {path}")
        return json.load(f)

def evaluate_numina(orchestrator, problems, max_problems=None):
    """
    Evaluate on NuminaMath balanced set
    
    Args:
        orchestrator: Orchestrator instance
        problems: List of NuminaMath problems
        max_problems: Limit number of problems (for testing)
    """
    if max_problems:
        problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name="NuminaMath_Balanced")
    metrics.start()
    
    total = len(problems)
    
    print(f"\n{'='*70}")
    print(f"Evaluating on {total} NuminaMath Problems")
    print(f"{'='*70}\n")
    
    for idx, problem_data in enumerate(tqdm(problems, desc="Solving NuminaMath")):
        problem = problem_data['problem']
        reference_answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')

        # Determine difficulty from source
        difficulty = determine_difficulty_from_source(source)

        try:
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem
            )
            solve_time = time.time() - start_time
            predicted_answer = result.get('answer', 'N/A')

            # Check correctness using unified utility
            is_correct = check_answer_correctness(reference_answer, predicted_answer)

            # P5: capture failure reason for error_summary (syntax/runtime/timeout/oom etc.)
            fail_reason = None
            if not is_correct or result.get('method') == 'all_failed':
                ex = result.get('execution_result') or result.get('error')
                if ex and isinstance(ex, str) and ('Error:' in ex or 'failed' in ex.lower()):
                    fail_reason = ex[:500]

            # Create result entry
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                reference_answer=reference_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                solve_time=solve_time,
                method=result.get('method', 'unknown'),
                difficulty=difficulty,
                source=source,
                error=fail_reason
            )
            
            metrics.add_result(eval_result)

            if (idx + 1) % 10 == 0:
                current_metrics = metrics.calculate_metrics()
                current_accuracy = current_metrics['accuracy']
                print(f"\nProgress: {idx+1}/{total} | Accuracy: {current_accuracy:.1f}%")
        except Exception as e:
            print(f"\nError on problem {idx} ({source}): {str(e)}")
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                reference_answer=reference_answer,
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
        filename='numina_balanced_results.json'
    )
    print(f"Results saved to: {output_path}")

    final_metrics = metrics.calculate_metrics()
    try:
        from evaluation.run_helpers import save_gradient_and_error_summary, print_gradient_summary
        grad_path = save_gradient_and_error_summary(
            final_metrics,
            [r.to_dict() for r in metrics.results],
            output_dir=RESULTS_DIR,
            dataset_name='NuminaMath_Balanced',
            filename='gradient_report_numina.json'
        )
        print(f"Gradient report saved to: {grad_path}")
        print_gradient_summary(final_metrics)
    except Exception as e:
        print(f"[Gradient report skip] {e}")

    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

def main():
    print("="*70)
    print("NuminaMath Balanced Set Benchmark")
    print("="*70)
    print("\nDataset: NuminaMath-1.5 Balanced Subset")
    print("Problems: 60 (10 easy, 20 medium, 30 hard)")
    print("Purpose: Development and mixed-difficulty testing")
    print("="*70)
    
    # Load problems
    print("\nLoading NuminaMath evaluation set...")
    problems = load_numina_eval()
    print(f"[OK] Loaded {len(problems)} problems")
    
    # Initialize orchestrator
    print("\nInitializing solver...")
    orchestrator = PipelineOrchestrator()
    
    # Run evaluation (MAX_PROBLEMS env = None for full 60, or set e.g. 5 for quick test)
    import os
    max_problems = os.environ.get("MAX_PROBLEMS")
    max_problems = int(max_problems) if max_problems is not None and max_problems.isdigit() else None
    print("\nStarting evaluation...")
    accuracy, results = evaluate_numina(
        orchestrator,
        problems,
        max_problems=max_problems
    )
    
    # Analysis
    print("\n" + "="*70)
    print("Performance Analysis")
    print("="*70)
    print(f"Your System: {accuracy:.2f}%")
    print("\nExpected performance ranges:")
    print("  Easy problems (Orca): 80-90%")
    print("  Medium problems (K-12): 60-70%")
    print("  Hard problems (Olympiad): 30-40%")
    print("="*70)

if __name__ == "__main__":
    main()
