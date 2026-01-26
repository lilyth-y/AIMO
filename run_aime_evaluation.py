"""
Run evaluation on AIME Validation Set (90 official AIME 2022-2024 problems)
- Official benchmark for AIME-level performance
- Standardized comparison across systems
"""

import sys
import os
sys.path.append('src')

import json
from pipeline.orchestrator import PipelineOrchestrator
from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult, 
    check_answer_correctness, extract_aime_answer
)
from tqdm import tqdm
import time

def load_aime_validation():
    """Load AIME validation set from several possible locations"""
    from evaluation.config import find_data_file, AIME_VALIDATION_FILE
    
    path = find_data_file(AIME_VALIDATION_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        print(f"Loaded AIME validation from: {path}")
        return json.load(f)

def evaluate_aime(orchestrator, problems, max_problems=None):
    """
    Evaluate on AIME validation set
    
    Args:
        orchestrator: Orchestrator instance
        problems: List of AIME problems
        max_problems: Limit number of problems (for testing)
    """
    if max_problems:
        problems = problems[:max_problems]
    
    metrics = EvaluationMetrics(dataset_name="AIME_Validation")
    metrics.start()
    
    total = len(problems)
    
    print(f"\n{'='*70}")
    print(f"Evaluating on {total} AIME Problems")
    print(f"{'='*70}\n")
    
    for idx, problem_data in enumerate(tqdm(problems, desc="Solving AIME")):
        problem = problem_data['problem']
        reference_solution = problem_data['solution']
        url = problem_data.get('url', '')
        
        try:
            # Solve with orchestrator
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem
            )
            solve_time = time.time() - start_time
            
            # Extract answer
            predicted_answer = result.get('answer', 'N/A')
            
            # Extract boxed answer from reference solution
            reference_answer = extract_aime_answer(reference_solution)
            
            # Check correctness
            is_correct = check_answer_correctness(reference_answer, predicted_answer)
            
            # Create result entry
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                reference_answer=reference_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                solve_time=solve_time,
                method=result.get('method', 'unknown'),
                difficulty='hard',  # AIME problems are hard by default
                source='aime',
                metadata={'url': url}
            )
            
            metrics.add_result(eval_result)
            
            # Progress update
            if (idx + 1) % 10 == 0:
                current_metrics = metrics.calculate_metrics()
                current_accuracy = current_metrics['accuracy']
                print(f"\nProgress: {idx+1}/{total} | Accuracy: {current_accuracy:.1f}%")
        
        except Exception as e:
            print(f"\nError on problem {idx}: {str(e)}")
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                is_correct=False,
                error=str(e),
                difficulty='hard',
                source='aime',
                metadata={'url': url}
            )
            metrics.add_result(eval_result)
    
    metrics.finish()
    
    # Print summary
    metrics.print_summary()
    
    # Save results
    from evaluation.config import ensure_dir, RESULTS_DIR
    ensure_dir(RESULTS_DIR)
    output_path = metrics.save_results(
        output_dir=str(RESULTS_DIR),
        filename='aime_validation_results.json'
    )
    
    print(f"Results saved to: {output_path}")
    
    final_metrics = metrics.calculate_metrics()
    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

def main():
    import argparse

    parser = argparse.ArgumentParser(description='AIME Validation Benchmark')
    parser.add_argument('--max-problems', type=int, default=None,
                        help='Limit number of problems to evaluate (for testing)')
    args = parser.parse_args()

    print("="*70)
    print("AIME Validation Benchmark")
    print("="*70)
    print("\nDataset: AI-MO/aimo-validation-aime")
    print("Problems: 90 official AIME 2022-2024")
    print("Level: AIME competition (high school, USA)")
    print("="*70)
    
    # Load AIME problems
    print("\nLoading AIME validation set...")
    problems = load_aime_validation()
    print(f"✅ Loaded {len(problems)} AIME problems")
    
    # Initialize orchestrator
    print("\nInitializing solver...")
    orchestrator = PipelineOrchestrator()
    
    # Run evaluation
    print("\nStarting evaluation...")
    accuracy, results = evaluate_aime(
        orchestrator,
        problems,
        max_problems=args.max_problems
    )
    
    # Compare with baseline
    print("\n" + "="*70)
    print("Comparison with Known Results")
    print("="*70)
    print(f"Your System: {accuracy:.2f}%")
    print(f"AIMO Winners (NuminaMath team): ~58% (29/50 on AIMO Prize)")
    print(f"GPT-4 (reported): ~45% on AIME")
    print("="*70)

if __name__ == "__main__":
    main()
