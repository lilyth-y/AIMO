import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.reasoning_utils import extract_answer

def run_evaluation():
    print("🚀 Starting Local AIMO Evaluation Pipeline...")
    
    # Load evaluation problems
    eval_file = os.path.join(os.path.dirname(__file__), "..", "data", "eval_data.jsonl")
    problems = []
    if os.path.exists(eval_file):
        with open(eval_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    problems.append(json.loads(line))
    else:
        print(f"❌ Evaluation file not found: {eval_file}")
        return

    print(f"📂 Loaded {len(problems)} problems from {eval_file}")

    orchestrator = PipelineOrchestrator()
    results = []

    # Limit to first 5 for quick testing initially
    test_limit = min(5, len(problems))
    print(f"⏳ Running evaluation on the first {test_limit} problems...")

    correct_count = 0
    total_time = 0.0

    for i in range(test_limit):
        prob = problems[i]
        problem_text = prob.get("query", "")
        # The reference answer might be deep in the dataset, but for now we just parse.
        # Often the last number in the solution is the answer.
        # Let's extract the reference answer if possible, or just keep it as Unknown.
        reference_answer = "Unknown"
        
        print(f"\n--- Problem {i+1}/{test_limit} ---")
        start_time = time.time()
        
        try:
            # Call Orchestrator
            # Domain and variables are usually extracted by Stage 1, we pass empty mostly
            result_dict = orchestrator.solve_problem(domain="math", variables={}, problem_text=problem_text)
            
            predicted_answer = result_dict.get('answer', "Failure")
            method = result_dict.get('method', "unknown")
            solution_text = result_dict.get('execution_result', "")
        except Exception as e:
            print(f"❌ Error solving problem {i}: {e}")
            predicted_answer = "Error"
            method = "error"
            solution_text = str(e)
            
        solve_time = time.time() - start_time
        total_time += solve_time
        
        # Determine strict correctness if reference answer is known
        is_correct = None
        
        results.append({
            "problem_id": i,
            "problem": problem_text,
            "reference_answer": reference_answer,
            "predicted_answer": str(predicted_answer),
            "is_correct": is_correct,
            "solve_time": round(solve_time, 2),
            "method": method,
            "difficulty": "medium",
            "source": "MATH500",
            "error": "Syntax Error" if "Error" in str(predicted_answer) else None,
            "solution": str(solution_text)
        })
        
        print(f"✅ Predict: {predicted_answer} (Time: {solve_time:.2f}s, Method: {method})")

        # Save incremental results for dashboard
        current_summary = {
            "total": test_limit,
            "processed": i + 1,
            "correct": correct_count,
            "accuracy": (correct_count / (i + 1)) * 100,
            "results": results
        }
        output_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "public", "results", "real_eval_results.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"dataset": "MATH500 (Live)", "summary": current_summary, "results": results}, f, indent=2, ensure_ascii=False)


    print(f"\n🎉 Evaluation Complete! Results saved to incremental path.")


if __name__ == "__main__":
    run_evaluation()
