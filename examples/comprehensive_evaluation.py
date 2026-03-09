"""
Comprehensive Evaluation Example
Demonstrates all advanced evaluation features:
- Advanced metrics with statistical significance
- Benchmarking and comparison
- Comprehensive reporting with visualizations
- Cross-validation
- Progress tracking
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from pipeline.orchestrator import PipelineOrchestrator
from evaluation.evaluation_utils import (
    EvaluationMetrics, EvaluationResult,
    check_answer_correctness, determine_difficulty_from_source
)
from evaluation.advanced_metrics import AdvancedEvaluator, ErrorCategorizer
from evaluation.benchmarking import BenchmarkManager, BenchmarkRun, CrossValidation
from evaluation.comprehensive_reporting import ComprehensiveReporter, ProgressTracker
from tqdm import tqdm
import time


def load_evaluation_data(max_problems: int = 20):
    """Load evaluation dataset"""
    from evaluation.config import find_data_file, NUMINA_EVAL_BALANCED_FILE
    
    try:
        path = find_data_file(NUMINA_EVAL_BALANCED_FILE)
        with open(path, 'r', encoding='utf-8') as f:
            problems = json.load(f)
            if max_problems:
                problems = problems[:max_problems]
            print(f"✅ Loaded {len(problems)} problems from {path}")
            return problems
    except FileNotFoundError as e:
        print(f"⚠️  Could not load evaluation data: {e}")
        print("Creating synthetic test data...")
        return create_synthetic_test_data(max_problems)


def create_synthetic_test_data(n_problems: int = 20):
    """Create synthetic test data for demonstration"""
    problems = []
    for i in range(n_problems):
        problem_type = ['easy', 'medium', 'hard'][i % 3]
        problems.append({
            'problem': f"Test problem {i+1}: What is {i+2} + {i+3}?",
            'answer': str((i+2) + (i+3)),
            'source': 'synthetic',
            'difficulty': problem_type
        })
    return problems


def run_comprehensive_evaluation(max_problems: int = 20, 
                                model_name: str = "OMI-1.0",
                                save_benchmark: bool = True):
    """
    Run comprehensive evaluation with all advanced features
    
    Args:
        max_problems: Number of problems to evaluate
        model_name: Name of the model being evaluated
        save_benchmark: Whether to save to benchmark database
    """
    
    print("="*80)
    print("COMPREHENSIVE EVALUATION")
    print("="*80)
    print(f"Model: {model_name}")
    print(f"Problems: {max_problems}")
    print("="*80 + "\n")
    
    # Load problems
    problems = load_evaluation_data(max_problems)
    
    # Initialize orchestrator
    print("\n⚙️  Initializing orchestrator...")
    orchestrator = PipelineOrchestrator()
    
    # Initialize evaluators
    basic_metrics = EvaluationMetrics(dataset_name=f"{model_name}_eval")
    advanced_evaluator = AdvancedEvaluator()
    
    basic_metrics.start()
    
    print(f"\n🚀 Starting evaluation on {len(problems)} problems...\n")
    
    # Evaluate each problem
    for idx, problem_data in enumerate(tqdm(problems, desc="Evaluating")):
        problem = problem_data['problem']
        reference_answer = problem_data.get('answer', '')
        source = problem_data.get('source', 'unknown')
        difficulty = problem_data.get('difficulty') or determine_difficulty_from_source(source)
        
        try:
            # Solve problem
            start_time = time.time()
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem,
                time_budget=60.0
            )
            solve_time = time.time() - start_time
            
            predicted_answer = result.get('answer', 'N/A')
            method = result.get('method', 'unknown')
            
            # Check correctness
            is_correct = check_answer_correctness(reference_answer, predicted_answer)
            
            # Add to basic metrics
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                reference_answer=reference_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                solve_time=solve_time,
                method=method,
                difficulty=difficulty,
                source=source
            )
            basic_metrics.add_result(eval_result)
            
            # Add to advanced evaluator
            advanced_evaluator.add_result(
                is_correct=is_correct,
                latency=solve_time,
                error_type=None if is_correct else 'wrong_answer',
                metadata={
                    'problem_id': idx,
                    'difficulty': difficulty,
                    'source': source,
                    'method': method
                }
            )
            
        except Exception as e:
            # Handle errors
            error_msg = str(e)
            error_type = ErrorCategorizer.categorize_error(error_msg)
            
            eval_result = EvaluationResult(
                problem_id=idx,
                problem=problem,
                is_correct=False,
                error=error_msg,
                difficulty=difficulty,
                source=source
            )
            basic_metrics.add_result(eval_result)
            
            advanced_evaluator.add_result(
                is_correct=False,
                latency=0.0,
                error_type=error_type,
                metadata={
                    'problem_id': idx,
                    'difficulty': difficulty,
                    'source': source,
                    'error_message': error_msg
                }
            )
    
    basic_metrics.finish()
    
    # Calculate all metrics
    print("\n" + "="*80)
    print("EVALUATION COMPLETE - CALCULATING METRICS")
    print("="*80 + "\n")
    
    # Basic metrics
    basic_summary = basic_metrics.calculate_metrics()
    basic_metrics.print_summary()
    
    # Advanced metrics
    print("\n" + "-"*80)
    print("ADVANCED METRICS")
    print("-"*80)
    
    try:
        advanced_summary = advanced_evaluator.calculate_comprehensive_metrics()
        
        print(f"\n📊 Statistical Analysis:")
        print(f"  Accuracy: {advanced_summary.accuracy:.4f}")
        print(f"  95% CI: ({advanced_summary.accuracy_ci[0]:.4f}, {advanced_summary.accuracy_ci[1]:.4f})")
        print(f"  F1 Score: {advanced_summary.f1_score:.4f}")
        
        print(f"\n⏱️  Latency Analysis:")
        print(f"  Average: {advanced_summary.avg_latency:.2f}s")
        print(f"  P50: {advanced_summary.p50_latency:.2f}s")
        print(f"  P95: {advanced_summary.p95_latency:.2f}s")
        print(f"  P99: {advanced_summary.p99_latency:.2f}s")
        
        if advanced_summary.error_types:
            print(f"\n🔍 Error Analysis:")
            for error_type, count in advanced_summary.error_types.items():
                percentage = advanced_summary.error_rate_by_category.get(error_type, 0) * 100
                print(f"  {error_type}: {count} ({percentage:.1f}%)")
    
    except Exception as e:
        print(f"⚠️  Could not calculate advanced metrics: {e}")
        print("This may be due to missing scipy. Install with: pip install scipy")
        advanced_summary = None
    
    # Save results
    print("\n" + "-"*80)
    print("SAVING RESULTS")
    print("-"*80)
    
    results_path = basic_metrics.save_results(
        output_dir="results",
        filename=f"{model_name}_comprehensive_eval.json"
    )
    print(f"✅ Basic results saved to: {results_path}")
    
    # Generate comprehensive report
    print("\n📊 Generating comprehensive report with visualizations...")
    try:
        reporter = ComprehensiveReporter(output_dir="reports")
        report_path = reporter.generate_full_report(
            results=[r.to_dict() for r in basic_metrics.results],
            metrics=basic_summary,
            report_name=f"{model_name}_evaluation"
        )
        print(f"✅ Comprehensive report generated: {report_path}")
    except Exception as e:
        print(f"⚠️  Could not generate report: {e}")
        print("This may be due to missing matplotlib/seaborn. Install with: pip install matplotlib seaborn")
    
    # Save to benchmark database
    if save_benchmark:
        print("\n" + "-"*80)
        print("SAVING TO BENCHMARK DATABASE")
        print("-"*80)
        
        try:
            benchmark_manager = BenchmarkManager(benchmark_dir="benchmarks")
            
            benchmark_run = BenchmarkRun(
                run_id=f"{model_name}_{int(time.time())}",
                model_name=model_name,
                dataset="numina_eval_balanced",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                accuracy=basic_summary['accuracy'],
                total_problems=basic_summary['total'],
                correct=basic_summary['correct'],
                avg_time=basic_summary['avg_solve_time'],
                metadata={
                    'error_count': basic_summary.get('error_count', 0),
                    'by_difficulty': basic_summary.get('by_difficulty', {}),
                    'by_source': basic_summary.get('by_source', {}),
                    'by_method': basic_summary.get('by_method', {})
                },
                accuracy_ci_lower=advanced_summary.accuracy_ci[0] * 100 if advanced_summary else None,
                accuracy_ci_upper=advanced_summary.accuracy_ci[1] * 100 if advanced_summary else None,
                p50_latency=advanced_summary.p50_latency if advanced_summary else None,
                p95_latency=advanced_summary.p95_latency if advanced_summary else None,
                easy_accuracy=basic_summary.get('by_difficulty', {}).get('easy', {}).get('accuracy'),
                medium_accuracy=basic_summary.get('by_difficulty', {}).get('medium', {}).get('accuracy'),
                hard_accuracy=basic_summary.get('by_difficulty', {}).get('hard', {}).get('accuracy')
            )
            
            benchmark_manager.add_run(benchmark_run)
            print(f"✅ Benchmark saved with ID: {benchmark_run.run_id}")
            
            # Generate leaderboard
            leaderboard_path = benchmark_manager.save_leaderboard("numina_eval_balanced")
            print(f"✅ Leaderboard saved to: {leaderboard_path}")
            
            # Export benchmark report
            try:
                report_path = benchmark_manager.export_benchmark_report(
                    "numina_eval_balanced",
                    output_format='markdown'
                )
                print(f"✅ Benchmark report saved to: {report_path}")
            except Exception as e:
                print(f"⚠️  Could not export benchmark report: {e}")
        
        except Exception as e:
            print(f"⚠️  Could not save to benchmark database: {e}")
    
    # Track progress
    print("\n" + "-"*80)
    print("TRACKING PROGRESS")
    print("-"*80)
    
    try:
        tracker = ProgressTracker(tracking_file="progress_tracking.json")
        tracker.add_run({
            'model': model_name,
            'accuracy': basic_summary['accuracy'],
            'total': basic_summary['total'],
            'correct': basic_summary['correct'],
            'avg_time': basic_summary['avg_solve_time']
        })
        print("✅ Progress tracked")
    except Exception as e:
        print(f"⚠️  Could not track progress: {e}")
    
    # Final summary
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"✅ Evaluated {basic_summary['total']} problems")
    print(f"✅ Accuracy: {basic_summary['accuracy']:.2f}%")
    print(f"✅ Correct: {basic_summary['correct']}/{basic_summary['total']}")
    print(f"✅ Average time: {basic_summary['avg_solve_time']:.2f}s")
    
    if advanced_summary:
        print(f"✅ 95% CI: ({advanced_summary.accuracy_ci[0]*100:.2f}%, {advanced_summary.accuracy_ci[1]*100:.2f}%)")
        print(f"✅ P95 latency: {advanced_summary.p95_latency:.2f}s")
    
    print("="*80)
    
    return {
        'basic_metrics': basic_summary,
        'advanced_metrics': advanced_summary,
        'results_path': results_path
    }


def demo_cross_validation(problems: list, evaluate_fn):
    """Demo cross-validation functionality"""
    print("\n" + "="*80)
    print("CROSS-VALIDATION DEMO")
    print("="*80 + "\n")
    
    cv = CrossValidation(n_folds=5, random_seed=42)
    
    print(f"Running 5-fold cross-validation on {len(problems)} problems...")
    
    # Note: This is a simplified demo
    # In practice, you'd train/fine-tune on train set and evaluate on test set
    
    cv_results = cv.evaluate_with_cv(problems, evaluate_fn)
    
    print(f"\n📊 Cross-Validation Results:")
    print(f"  Mean Accuracy: {cv_results['mean_accuracy']:.4f}")
    print(f"  Std Accuracy: {cv_results['std_accuracy']:.4f}")
    print(f"  Min Accuracy: {cv_results['min_accuracy']:.4f}")
    print(f"  Max Accuracy: {cv_results['max_accuracy']:.4f}")
    print(f"\n  Fold Accuracies: {cv_results['fold_accuracies']}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Evaluation Demo')
    parser.add_argument('--max-problems', type=int, default=20,
                       help='Maximum number of problems to evaluate')
    parser.add_argument('--model-name', type=str, default='OMI-1.0',
                       help='Name of the model being evaluated')
    parser.add_argument('--no-benchmark', action='store_true',
                       help='Do not save to benchmark database')
    
    args = parser.parse_args()
    
    # Run comprehensive evaluation
    results = run_comprehensive_evaluation(
        max_problems=args.max_problems,
        model_name=args.model_name,
        save_benchmark=not args.no_benchmark
    )
    
    print("\n✅ Comprehensive evaluation complete!")
    print(f"\nResults saved to: {results['results_path']}")
    print("\nNext steps:")
    print("  1. Review the comprehensive report in the 'reports/' directory")
    print("  2. Check the benchmark leaderboard in 'benchmarks/' directory")
    print("  3. Compare with other models using BenchmarkManager")
    print("  4. Track progress over time using ProgressTracker")


if __name__ == "__main__":
    main()
