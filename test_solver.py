"""
Quick test of the solver with a simple problem
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline.orchestrator import PipelineOrchestrator

def main():
    print("="*70)
    print("Testing Solver with Simple Problem")
    print("="*70)
    
    # Simple test problem
    problem = "What is 15 + 27?"
    
    print(f"\nProblem: {problem}\n")
    
    # Initialize orchestrator
    print("Initializing solver...")
    orchestrator = PipelineOrchestrator()
    print("Solver initialized.\n")
    
    # Solve
    print("Solving...")
    result = orchestrator.solve_problem(
        domain="general_math",
        variables={},
        problem_text=problem
    )
    
    print("\n" + "="*70)
    print("Result:")
    print("="*70)
    print(f"Answer: {result.get('answer', 'N/A')}")
    print(f"Method: {result.get('method', 'unknown')}")
    if 'code' in result:
        print(f"\nGenerated Code:\n{result['code']}")
    print("="*70)

if __name__ == "__main__":
    main()
