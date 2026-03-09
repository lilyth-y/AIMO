"""
Numina Training 5 Problems Evaluation
- Loads 5 problems from data/numina_training_5k.jsonl
- Runs pipeline (orchestrator) on each
- Reports metrics and reference solutions (proof)
"""

import sys
import os
import json
import time

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from evaluation.evaluation_utils import (
    EvaluationMetrics,
    EvaluationResult,
    check_answer_correctness,
    determine_difficulty_from_source,
)
from evaluation.config import find_data_file, NUMINA_TRAINING_FILE, ensure_dir, RESULTS_DIR


def load_5_from_numina_training():
    """Load first 5 problems from numina_training_5k.jsonl."""
    path = find_data_file(NUMINA_TRAINING_FILE)
    problems = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            problems.append(json.loads(line.strip()))
    return problems


def run_eval(use_orchestrator=True):
    """Run evaluation on 5 problems; optionally use real orchestrator."""
    problems = load_5_from_numina_training()
    print(f"Loaded {len(problems)} problems from Numina training set.\n")

    metrics = EvaluationMetrics(dataset_name="NuminaTraining_5")
    metrics.start()

    if use_orchestrator:
        try:
            from pipeline.orchestrator import PipelineOrchestrator
            orchestrator = PipelineOrchestrator()
        except Exception as e:
            print(f"Orchestrator init failed: {e}")
            print("Running in reference-only mode (no solver).\n")
            use_orchestrator = False

    results_detail = []

    for idx, item in enumerate(problems):
        problem = item["problem"]
        reference_answer = item.get("answer", "")
        solution = item.get("solution", "")
        problem_type = item.get("problem_type", "")
        source = item.get("source", "unknown")

        # Short problem preview (first 120 chars, no newlines)
        problem_preview = problem.replace("\n", " ").strip()[:120] + "..."

        print(f"\n{'='*70}")
        print(f"Problem {idx+1}/5  [{problem_type}]")
        print(f"{'='*70}")
        print(f"Problem: {problem_preview}")
        print(f"Reference answer: {reference_answer}")

        predicted_answer = "N/A"
        solve_time = 0.0
        method = "none"
        error_msg = None

        if use_orchestrator:
            try:
                start = time.time()
                result = orchestrator.solve_problem(
                    domain="general_math",
                    variables={},
                    problem_text=problem,
                    time_budget=90.0,
                )
                solve_time = time.time() - start
                predicted_answer = result.get("answer", "N/A")
                method = result.get("method", "unknown")
                if result.get("error"):
                    error_msg = str(result.get("error"))[:300]
            except Exception as e:
                error_msg = str(e)[:300]
                predicted_answer = "N/A"

        print(f"Predicted answer: {predicted_answer}")
        if error_msg:
            print(f"Error: {error_msg}")

        is_correct = check_answer_correctness(reference_answer, predicted_answer) if use_orchestrator else False
        difficulty = determine_difficulty_from_source(source)

        metrics.add_result(
            EvaluationResult(
                problem_id=idx,
                problem=problem,
                reference_answer=reference_answer,
                predicted_answer=predicted_answer,
                is_correct=is_correct,
                solve_time=solve_time,
                method=method,
                difficulty=difficulty,
                source=source,
                error=error_msg,
            )
        )

        # Reference solution (proof) - first 500 chars for summary
        proof_preview = (solution or "").replace("\n", " ").strip()[:500]
        if len((solution or "").strip()) > 500:
            proof_preview += "..."

        results_detail.append({
            "problem_id": idx + 1,
            "problem_type": problem_type,
            "reference_answer": reference_answer,
            "predicted_answer": predicted_answer,
            "is_correct": is_correct,
            "solve_time": solve_time,
            "proof_preview": proof_preview,
        })

        status = "[OK] CORRECT" if is_correct else "[X] WRONG"
        print(f"Result: {status}")

    metrics.finish()

    # Summary metrics
    print("\n" + "="*70)
    print("METRICS SUMMARY")
    print("="*70)
    m = metrics.calculate_metrics()
    print(f"Total:        {m['total']}")
    print(f"Correct:       {m['correct']}")
    print(f"Incorrect:    {m['incorrect']}")
    print(f"Accuracy:     {m['accuracy']:.2f}%")
    print(f"Avg time:      {m['avg_solve_time']:.2f}s")
    print("="*70)

    # Proof section: reference solutions for each problem
    print("\n" + "="*70)
    print("REFERENCE SOLUTIONS (PROOF)")
    print("="*70)
    for r in results_detail:
        print(f"\n--- Problem {r['problem_id']} [{r['problem_type']}] ---")
        print(f"Reference answer: {r['reference_answer']}")
        print(f"Proof (excerpt):\n{r['proof_preview']}\n")

    # Save results
    ensure_dir(RESULTS_DIR)
    out_path = os.path.join(RESULTS_DIR, "numina_training_5_eval.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": m,
            "results_detail": results_detail,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {out_path}")

    return m["accuracy"], results_detail


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Eval 5 problems from Numina training")
    p.add_argument("--reference-only", action="store_true", help="Skip solver; output refs and proof only")
    args = p.parse_args()
    run_eval(use_orchestrator=not args.reference_only)
