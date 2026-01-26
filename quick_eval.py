"""
Quick evaluation with minimal memory footprint
Loads model once and keeps it in memory for multiple problems
"""

import sys
import os
import json

# Add project root and src to path
project_root = os.path.dirname(__file__)
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
                print("✅ CORRECT")
            else:
                print("❌ WRONG")
            
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
            print(f"❌ ERROR: {str(e)}")
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
    return final_metrics['accuracy'], [r.to_dict() for r in metrics.results]

if __name__ == "__main__":
    print("Loading problems...")
    problems = load_numina_eval()
    print(f"Loaded {len(problems)} problems")
    
    print("\nInitializing solver...")
    orchestrator = PipelineOrchestrator()
    print("Solver ready!")
    
    # Run quick eval
    accuracy, results = evaluate_quick(orchestrator, problems, max_problems=5)
    
    print(f"\n✅ Evaluation completed. Accuracy: {accuracy:.2f}%")
