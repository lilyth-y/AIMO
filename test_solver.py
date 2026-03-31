"""
Docker/CI entrypoint smoke test: trivial problem through PipelineOrchestrator.

`entrypoint.sh` calls this from the repo root (`WORKDIR` /app in the image).
"""
import os
import sys

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))

from pipeline.orchestrator import PipelineOrchestrator  # noqa: E402


def main() -> None:
    print("=" * 70)
    print("Testing Solver with Simple Problem")
    print("=" * 70)

    problem = "What is 15 + 27?"
    print(f"\nProblem: {problem}\n")

    print("Initializing solver...")
    orchestrator = PipelineOrchestrator()
    print("Solver initialized.\n")

    print("Solving...")
    result = orchestrator.solve_problem(
        domain="general_math",
        variables={},
        problem_text=problem,
    )

    print("\n" + "=" * 70)
    print("Result:")
    print("=" * 70)
    print(f"Answer: {result.get('answer', 'N/A')}")
    print(f"Method: {result.get('method', 'unknown')}")
    if "code" in result:
        print(f"\nGenerated Code:\n{result['code']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
