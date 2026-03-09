"""Quick demo of revolving resolution without LLM dependencies."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import directly from the revolving_resolution module to avoid heavy pipeline dependencies
from pipeline import revolving_resolution

# Now import the classes
RevolvingResolver = revolving_resolution.RevolvingResolver
StrategySelector = revolving_resolution.StrategySelector
MultiPathExplorer = revolving_resolution.MultiPathExplorer
ProblemContext = revolving_resolution.ProblemContext
StrategyType = revolving_resolution.StrategyType
ResolutionStatus = revolving_resolution.ResolutionStatus

import random
import time
from typing import Dict


def simple_solver(problem_text: str, strategy: StrategyType) -> Dict:
    """
    Simple mock solver that demonstrates the revolving resolution framework.
    Returns: Dict with 'answer', 'confidence', and 'metadata'
    """
    time.sleep(0.1)  # Simulate computation time
    
    problem_text = problem_text.lower()
    
    # Simulate different strategies working better for different problems
    if "+" in problem_text and strategy == StrategyType.DIRECT_COMPUTATION:
        # Direct computation works well for addition
        parts = problem_text.split("+")
        if len(parts) == 2:
            try:
                a = int(''.join(c for c in parts[0] if c.isdigit()))
                b = int(''.join(c for c in parts[1] if c.isdigit()))
                return {'answer': str(a + b), 'confidence': 0.95, 'verified': True, 'metadata': '{"method": "addition"}'}
            except:
                pass
    
    elif "x" in problem_text and "=" in problem_text:
        # Symbolic solving works for equations
        if strategy == StrategyType.SYMBOLIC_SOLVING:
            # Solve 2x + 5 = 13 -> x = 4
            if "2x + 5 = 13" in problem_text:
                return {'answer': "4", 'confidence': 0.90, 'verified': True, 'metadata': '{"method": "symbolic_algebra"}'}
        elif strategy == StrategyType.ALGEBRAIC_MANIPULATION:
            # Alternative approach
            if "2x + 5 = 13" in problem_text:
                return {'answer': "4", 'confidence': 0.85, 'verified': True, 'metadata': '{"method": "manual_algebra"}'}
    
    elif "sum" in problem_text and "first" in problem_text:
        # Pattern matching works for series
        if strategy == StrategyType.PATTERN_MATCHING:
            if "first 10 natural numbers" in problem_text:
                return {'answer': "55", 'confidence': 0.88, 'verified': True, 'metadata': '{"method": "arithmetic_series"}'}
        elif strategy == StrategyType.DIRECT_COMPUTATION:
            return {'answer': "55", 'confidence': 0.75, 'verified': True, 'metadata': '{"method": "brute_force_sum"}'}
    
    elif "f(x)" in problem_text and "f(3)" in problem_text:
        # Direct computation for function evaluation
        if strategy == StrategyType.DIRECT_COMPUTATION:
            # f(x) = x^2 + 2x + 1, f(3) = 9 + 6 + 1 = 16
            return {'answer': "16", 'confidence': 0.92, 'verified': True, 'metadata': '{"method": "function_eval"}'}
    
    elif "triangle" in problem_text and "area" in problem_text:
        # Theorem application for geometry
        if strategy == StrategyType.THEOREM_APPLICATION:
            # 3-4-5 right triangle, area = 6
            if "3" in problem_text and "4" in problem_text and "5" in problem_text:
                return {'answer': "6", 'confidence': 0.90, 'verified': True, 'metadata': '{"method": "right_triangle_formula"}'}
    
    # Fallback: random guess with low confidence
    confidence = random.uniform(0.2, 0.4)
    answer = str(random.randint(1, 100))
    return {'answer': answer, 'confidence': confidence, 'verified': False, 'metadata': f'{{"method": "guess", "strategy": "{strategy.value}"}}'}


def demo_basic_revolving():
    """Demo basic revolving resolution."""
    print("\n" + "="*80)
    print("DEMO 1: Basic Revolving Resolution")
    print("="*80 + "\n")
    
    resolver = RevolvingResolver(
        max_iterations=3,
        confidence_threshold=0.85,
        time_budget=10.0
    )
    
    problems = [
        ("What is 15 + 27?", "arithmetic", "easy"),
        ("Solve for x: 2x + 5 = 13", "algebra", "easy"),
        ("Find the sum of the first 10 natural numbers", "arithmetic", "medium"),
        ("If f(x) = x^2 + 2x + 1, what is f(3)?", "algebra", "easy"),
        ("A triangle has sides of length 3, 4, and 5. What is its area?", "geometry", "easy"),
    ]
    
    results = []
    for problem_text, domain, difficulty in problems:
        print(f"🔹 Problem: {problem_text}")
        
        context = ProblemContext(
            problem_text=problem_text,
            domain=domain,
            difficulty=difficulty,
            features={
                'has_equations': 'x' in problem_text or 'f(x)' in problem_text,
                'has_numbers': any(c.isdigit() for c in problem_text),
                'requires_approximation': False,
            }
        )
        
        answer, status, metadata = resolver.resolve(context, simple_solver)
        
        print(f"   ✅ Answer: {answer}")
        print(f"   Status: {status.value}")
        print(f"   Attempts: {metadata.get('total_attempts', 0)}")
        print(f"   Best Confidence: {metadata.get('best_confidence', 0):.2f}")
        print(f"   Time: {metadata.get('total_time', 0):.2f}s")
        print()
        
        results.append({
            'problem': problem_text,
            'answer': answer,
            'status': status,
            'attempts': metadata.get('total_attempts', 0)
        })
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    successful = sum(1 for r in results if r['status'] == ResolutionStatus.SUCCESS)
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"📊 Average Attempts: {sum(r['attempts'] for r in results) / len(results):.1f}")
    

def demo_multipath():
    """Demo multi-path exploration."""
    print("\n" + "="*80)
    print("DEMO 2: Multi-Path Exploration")
    print("="*80 + "\n")
    
    explorer = MultiPathExplorer(n_paths=3)
    
    problem = "What is 15 + 27?"
    print(f"🔹 Problem: {problem}")
    print(f"🔹 Exploring {explorer.n_paths} independent solution paths...\n")
    
    context = ProblemContext(
        problem_text=problem,
        domain="arithmetic",
        difficulty="easy",
        features={'has_numbers': True}
    )
    
    answer, confidence, metadata = explorer.explore(context, simple_solver)
    
    print(f"\n📊 Results:")
    print(f"   Answer: {answer}")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Consensus Reached: {metadata.get('consensus', False)}")
    print(f"   All Answers: {metadata.get('all_answers', [])}")
    all_confs = [f"{c:.2f}" for c in metadata.get('all_confidences', [])]
    print(f"   All Confidences: {all_confs}")


def demo_strategy_comparison():
    """Demo strategy effectiveness comparison."""
    print("\n" + "="*80)
    print("DEMO 3: Strategy Effectiveness Analysis")
    print("="*80 + "\n")
    
    selector = StrategySelector()
    
    # Simulate strategy performance data
    test_cases = [
        ("15 + 27", StrategyType.DIRECT_COMPUTATION, True, 0.95),
        ("2x + 5 = 13", StrategyType.SYMBOLIC_SOLVING, True, 0.90),
        ("2x + 5 = 13", StrategyType.ALGEBRAIC_MANIPULATION, True, 0.85),
        ("sum of first 10", StrategyType.PATTERN_MATCHING, True, 0.88),
        ("f(3) for f(x)=x^2", StrategyType.DIRECT_COMPUTATION, True, 0.92),
        ("triangle area", StrategyType.THEOREM_APPLICATION, True, 0.90),
    ]
    
    print("🧪 Testing different strategies on various problems:\n")
    
    for problem, strategy, success, conf in test_cases:
        features = {
            'has_equations': 'x' in problem,
            'has_numbers': any(c.isdigit() for c in problem),
        }
        
        print(f"   {'✅' if success else '❌'} {problem[:30]:30} → {strategy.value:25} (conf: {conf:.2f})")
    
    print("\n💡 The StrategySelector intelligently chooses strategies based on:")
    print("   - Historical success rates (40%)")
    print("   - Domain compatibility (30%)")
    print("   - Feature matching (20%)")
    print("   - Difficulty appropriateness (10%)")


def main():
    """Run all demos."""
    print("\n" + "🎯"*40)
    print("REVOLVING RESOLUTION FRAMEWORK - QUICK DEMO")
    print("🎯"*40)
    
    demo_basic_revolving()
    demo_multipath()
    demo_strategy_comparison()
    
    print("\n" + "="*80)
    print("✨ All Demos Complete!")
    print("="*80)
    print("\n💡 Key Features Demonstrated:")
    print("   - Iterative problem solving with strategy adaptation")
    print("   - Multi-path exploration for confidence boosting")
    print("   - Intelligent strategy selection")
    print("   - Comprehensive metadata tracking")
    print("   - Early stopping on high confidence")
    print("\n📚 See docs/MATHEMATICAL_SOLUTION_RESEARCH_TREE.md for detailed docs")
    print()


if __name__ == "__main__":
    main()
