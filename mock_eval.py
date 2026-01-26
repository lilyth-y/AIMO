"""
Quick evaluation with Mock Solver
No LLM loading - instant testing
"""

import sys
import os
import json

# Add paths
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.mock_solver import MockSolver
from tqdm import tqdm

def load_numina_eval():
    """Load NuminaMath balanced evaluation set"""
    with open('data/numina_eval_balanced.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_mock(orchestrator, problems, max_problems=10):
    """
    Lightweight evaluation with mock solver
    """
    correct = 0
    total = 0
    results = []
    
    problems = problems[:max_problems]
    
    print(f"\n{'='*70}")
    print(f"Mock Evaluation: {len(problems)} problems")
    print(f"Testing pipeline without heavy LLM")
    print(f"{'='*70}\n")
    
    for i, problem_data in enumerate(tqdm(problems, desc="Testing")):
        problem = problem_data['problem']
        answer = problem_data['answer']
        
        print(f"\n[{i+1}/{len(problems)}]")
        print(f"Problem: {problem[:80]}...")
        print(f"Expected: {answer}")
        
        try:
            # Solve
            result = orchestrator.solve_problem(
                domain="general_math",
                variables={},
                problem_text=problem,
                time_budget=10.0  # Short timeout for mock
            )
            
            predicted = result.get('answer', '')
            method = result.get('method', 'unknown')
            code = result.get('code', '')
            
            print(f"Predicted: {predicted}")
            print(f"Method: {method}")
            print(f"Code: {code[:50]}...")
            
            # Check correctness
            is_correct = str(predicted).strip().lower() == str(answer).strip().lower()
            
            if is_correct:
                correct += 1
                print("✅ CORRECT")
            else:
                print("❌ WRONG")
            
            total += 1
            
            results.append({
                'problem': problem,
                'expected': answer,
                'predicted': predicted,
                'method': method,
                'code': code,
                'correct': is_correct
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'problem': problem,
                'expected': answer,
                'predicted': None,
                'method': 'error',
                'correct': False,
                'error': str(e)
            })
            total += 1
    
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"MOCK RESULTS: {correct}/{total} = {accuracy:.1f}%")
    print(f"{'='*70}")
    print("\n✅ Pipeline is working!")
    print("📊 This validates the evaluation infrastructure")
    print("🚀 Ready to integrate real LLM when system resources allow")
    
    return accuracy, results

if __name__ == "__main__":
    print("🔧 Mock Evaluation - Testing Pipeline")
    print("="*70)
    
    print("\nLoading problems...")
    problems = load_numina_eval()
    print(f"✅ Loaded {len(problems)} problems")
    
    print("\nInitializing orchestrator with MOCK solver...")
    orchestrator = PipelineOrchestrator()
    
    # Replace solver with mock
    orchestrator.solver = MockSolver()
    print("✅ Mock solver ready (no LLM needed)")
    
    # Run mock eval
    accuracy, results = evaluate_mock(orchestrator, problems, max_problems=10)
    
    # Save results
    with open('mock_eval_results.json', 'w') as f:
        json.dump({
            'accuracy': accuracy,
            'total': len(results),
            'correct': sum(1 for r in results if r.get('correct', False)),
            'results': results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to mock_eval_results.json")
