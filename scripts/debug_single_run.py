"""1문항만 풀고 생성 코드 + 실행 결과를 출력해 32 출처 확인."""
import sys
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

import json
from pipeline.orchestrator import PipelineOrchestrator
from evaluation.config import find_data_file

def main():
    with open(find_data_file("numina_eval_balanced.json"), "r", encoding="utf-8") as f:
        problems = json.load(f)
    problem_data = problems[0]
    problem_text = problem_data["problem"]
    ref_answer = problem_data.get("answer", "")

    print("=" * 60)
    print("REF ANSWER:", ref_answer)
    print("=" * 60)
    print("PROBLEM (first 300 chars):", problem_text[:300])
    print("=" * 60)

    orch = PipelineOrchestrator()
    result = orch.solve_problem(
        domain="general_math",
        variables={},
        problem_text=problem_text,
        time_budget=60.0,
    )

    print("\n--- RETURNED answer ---")
    print(result.get("answer", "N/A"))
    print("\n--- RETURNED execution_result ---")
    print(repr(result.get("execution_result", "")))
    print("\n--- RETURNED code (first 2000 chars) ---")
    code = result.get("code") or ""
    print(code[:2000] if code else "(none)")
    if code and len(code) > 2000:
        print("... [truncated]")
    print("\n--- RETURNED extracted_answer ---")
    print(repr(result.get("extracted_answer", "")))
    print("\n--- DONE ---")

if __name__ == "__main__":
    main()
