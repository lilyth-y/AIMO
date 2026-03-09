"""
Revolving Resolution Example
Demonstrates the iterative problem-solving framework with strategy adaptation
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from pipeline.revolving_resolution import (
    RevolvingResolver, MultiPathExplorer, AdaptiveLearner,
    ProblemContext, StrategyType, ResolutionStatus
)
from pipeline.orchestrator import PipelineOrchestrator
import time


def create_problem_context(problem_text: str) -> ProblemContext:
    """Create enriched problem context"""
    # Simple feature extraction
    features = {
        'has_equations': any(op in problem_text for op in ['=', 'x', 'y']),
        'has_numbers': any(c.isdigit() for c in problem_text),
        'requires_approximation': 'approximately' in problem_text.lower(),
        'has_pattern': 'sequence' in problem_text.lower() or 'pattern' in problem_text.lower(),
        'is_simple_arithmetic': all(word in problem_text.lower() for word in ['what', 'is'])
    }
    
    # Determine domain
    domain = 'general_math'
    if 'geometry' in problem_text.lower() or 'triangle' in problem_text.lower():
        domain = 'geometry'
    elif 'prime' in problem_text.lower() or 'divisible' in problem_text.lower():
        domain = 'number_theory'
    elif 'probability' in problem_text.lower() or 'choose' in problem_text.lower():
        domain = 'combinatorics'
    
    # Estimate difficulty
    difficulty = 'easy'
    if len(problem_text.split()) > 30:
        difficulty = 'hard'
    elif len(problem_text.split()) > 15:
        difficulty = 'medium'
    
    return ProblemContext(
        problem_text=problem_text,
        domain=domain,
        difficulty=difficulty,
        features=features,
        constraints=[],
        keywords=problem_text.lower().split()[:10]
    )


def solver_function(problem_text: str, strategy: StrategyType) -> dict:
    """
    Mock solver function that uses orchestrator
    In real implementation, this would route to different solvers based on strategy
    """
    orchestrator = PipelineOrchestrator()
    
    try:
        result = orchestrator.solve_problem(
            domain="general_math",
            variables={},
            problem_text=problem_text,
            time_budget=30.0
        )
        
        return {
            'answer': result.get('answer', 'N/A'),
            'confidence': result.get('confidence', 0.5),
            'verified': result.get('answer', 'N/A') != 'N/A',
            'steps': result.get('steps', []),
            'metadata': {'strategy_used': strategy.value}
        }
    except Exception as e:
        return {
            'answer': None,
            'confidence': 0.0,
            'verified': False,
            'error': str(e)
        }


def demo_revolving_resolution():
    """Demonstrate revolving resolution framework"""
    print("="*80)
    print("REVOLVING RESOLUTION FRAMEWORK DEMO")
    print("="*80)
    
    # Example problems
    problems = [
        "What is 15 + 27?",
        "Solve for x: 2x + 5 = 13",
        "Find the sum of the first 10 natural numbers",
        "If f(x) = x^2 + 2x + 1, what is f(3)?",
        "A triangle has sides of length 3, 4, and 5. What is its area?"
    ]
    
    # Initialize resolver
    resolver = RevolvingResolver(
        max_iterations=3,
        confidence_threshold=0.8,
        time_budget=60.0
    )
    
    print("\n🔄 Testing Revolving Resolution on Multiple Problems\n")
    
    results = []
    for i, problem in enumerate(problems, 1):
        print(f"\n{'─'*80}")
        print(f"Problem {i}: {problem}")
        print(f"{'─'*80}")
        
        # Create problem context
        context = create_problem_context(problem)
        print(f"Domain: {context.domain} | Difficulty: {context.difficulty}")
        print(f"Features: {context.features}")
        
        # Solve with revolving resolution
        start_time = time.time()
        answer, status, metadata = resolver.resolve(context, solver_function)
        solve_time = time.time() - start_time
        
        print(f"\n📊 Resolution Result:")
        print(f"  Status: {status.value}")
        print(f"  Answer: {answer}")
        print(f"  Time: {solve_time:.2f}s")
        print(f"  Attempts: {metadata['total_attempts']}")
        print(f"  Strategies Tried: {metadata['strategies_tried']}")
        print(f"  Best Confidence: {metadata['best_confidence']:.2f}")
        print(f"  Verified Attempts: {metadata['verified_attempts']}")
        
        results.append({
            'problem': problem,
            'answer': answer,
            'status': status.value,
            'time': solve_time,
            'attempts': metadata['total_attempts']
        })
        
        # Print detailed attempt information
        if metadata['all_attempts']:
            print(f"\n  📝 Attempt Details:")
            for j, attempt in enumerate(metadata['all_attempts'], 1):
                status_icon = "✅" if attempt['verified'] else "❌"
                print(f"    {j}. {status_icon} {attempt['strategy']} "
                      f"(confidence: {attempt['confidence']:.2f}, "
                      f"time: {attempt['time']:.2f}s)")
                if attempt.get('error'):
                    print(f"       Error: {attempt['error'][:100]}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    avg_time = sum(r['time'] for r in results) / len(results)
    avg_attempts = sum(r['attempts'] for r in results) / len(results)
    
    print(f"Total Problems: {len(results)}")
    print(f"Successful: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"Average Time: {avg_time:.2f}s")
    print(f"Average Attempts: {avg_attempts:.1f}")
    
    return results


def demo_multipath_exploration():
    """Demonstrate multi-path exploration"""
    print("\n\n" + "="*80)
    print("MULTI-PATH EXPLORATION DEMO")
    print("="*80)
    
    problem = "Solve for x: 3x - 7 = 14"
    print(f"\nProblem: {problem}")
    
    context = create_problem_context(problem)
    explorer = MultiPathExplorer(n_paths=3)
    
    print("\n🔀 Exploring Multiple Solution Paths...")
    
    answer, confidence, metadata = explorer.explore(
        context,
        solver_function,
        strategies=[
            StrategyType.DIRECT_COMPUTATION,
            StrategyType.ALGEBRAIC_MANIPULATION,
            StrategyType.SYMBOLIC_SOLVING
        ]
    )
    
    print(f"\n📊 Multi-Path Result:")
    print(f"  Answer: {answer}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Consensus: {metadata.get('consensus', False)}")
    print(f"  Strategies Used: {metadata.get('strategies', [])}")
    
    if 'answer_distribution' in metadata:
        print(f"  Answer Distribution: {metadata['answer_distribution']}")


def demo_adaptive_learning():
    """Demonstrate adaptive learning"""
    print("\n\n" + "="*80)
    print("ADAPTIVE LEARNING DEMO")
    print("="*80)
    
    learner = AdaptiveLearner()
    
    # Simulate learning from multiple attempts
    print("\n📚 Simulating Learning from Solution Attempts...")
    
    # Record some attempts
    attempts = [
        ({'domain': 'algebra', 'difficulty': 'easy', 'has_equations': True}, 
         StrategyType.ALGEBRAIC_MANIPULATION, True, 0.9),
        ({'domain': 'algebra', 'difficulty': 'easy', 'has_equations': True}, 
         StrategyType.SYMBOLIC_SOLVING, True, 0.95),
        ({'domain': 'algebra', 'difficulty': 'easy', 'has_equations': True}, 
         StrategyType.DIRECT_COMPUTATION, False, 0.3),
        ({'domain': 'geometry', 'difficulty': 'medium', 'has_equations': False}, 
         StrategyType.THEOREM_APPLICATION, True, 0.85),
        ({'domain': 'geometry', 'difficulty': 'medium', 'has_equations': False}, 
         StrategyType.NUMERICAL_APPROXIMATION, False, 0.4),
    ]
    
    for features, strategy, success, confidence in attempts:
        learner.record_attempt(features, strategy, success, confidence)
        status = "✅ Success" if success else "❌ Failure"
        print(f"  {status}: {strategy.value} on {features['domain']} "
              f"(confidence: {confidence:.2f})")
    
    # Get recommendations
    print("\n💡 Getting Strategy Recommendations...")
    
    test_features = [
        {'domain': 'algebra', 'difficulty': 'easy', 'has_equations': True},
        {'domain': 'geometry', 'difficulty': 'medium', 'has_equations': False}
    ]
    
    for features in test_features:
        recommended = learner.get_recommended_strategies(features, n=3)
        print(f"\n  For {features['domain']} ({features['difficulty']}):")
        for i, strategy in enumerate(recommended, 1):
            print(f"    {i}. {strategy.value}")
    
    # Export knowledge
    print("\n💾 Exporting Learned Knowledge...")
    learner.export_knowledge("adaptive_knowledge.json")
    print("  Knowledge exported to: adaptive_knowledge.json")


def demo_strategy_comparison():
    """Compare different strategies on the same problem"""
    print("\n\n" + "="*80)
    print("STRATEGY COMPARISON DEMO")
    print("="*80)
    
    problem = "What is the sum of all integers from 1 to 100?"
    print(f"\nProblem: {problem}")
    
    context = create_problem_context(problem)
    
    strategies = [
        StrategyType.DIRECT_COMPUTATION,
        StrategyType.ALGEBRAIC_MANIPULATION,
        StrategyType.PATTERN_MATCHING
    ]
    
    print("\n🔬 Testing Different Strategies...\n")
    
    results = []
    for strategy in strategies:
        print(f"  Testing: {strategy.value}")
        start_time = time.time()
        
        try:
            result = solver_function(problem, strategy)
            solve_time = time.time() - start_time
            
            print(f"    ✅ Answer: {result.get('answer', 'N/A')}")
            print(f"    ⏱️  Time: {solve_time:.4f}s")
            print(f"    📊 Confidence: {result.get('confidence', 0):.2f}")
            
            results.append({
                'strategy': strategy.value,
                'answer': result.get('answer'),
                'time': solve_time,
                'confidence': result.get('confidence', 0)
            })
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
        
        print()
    
    # Summary
    if results:
        print("📊 Strategy Comparison Summary:")
        print(f"{'Strategy':<30} {'Time (s)':<12} {'Confidence':<12}")
        print("─" * 54)
        for r in results:
            print(f"{r['strategy']:<30} {r['time']:<12.4f} {r['confidence']:<12.2f}")


def main():
    """Run all demos"""
    print("\n" + "🎯"*40)
    print("REVOLVING RESOLUTION FRAMEWORK - COMPREHENSIVE DEMO")
    print("🎯"*40 + "\n")
    
    # Demo 1: Revolving Resolution
    demo_revolving_resolution()
    
    # Demo 2: Multi-Path Exploration
    demo_multipath_exploration()
    
    # Demo 3: Adaptive Learning
    demo_adaptive_learning()
    
    # Demo 4: Strategy Comparison
    demo_strategy_comparison()
    
    print("\n" + "="*80)
    print("✅ ALL DEMOS COMPLETED")
    print("="*80)
    
    print("\n📖 Summary:")
    print("  1. Revolving Resolution: Iterative problem-solving with strategy adaptation")
    print("  2. Multi-Path Exploration: Parallel solution paths with consensus")
    print("  3. Adaptive Learning: Learning from experience to improve strategy selection")
    print("  4. Strategy Comparison: Analyzing different approaches systematically")
    
    print("\n💡 Key Benefits:")
    print("  • Increased success rate through multiple attempts")
    print("  • Intelligent strategy selection based on problem features")
    print("  • Automatic learning and adaptation from experience")
    print("  • Comprehensive metadata for analysis and debugging")
    
    print("\n🚀 Next Steps:")
    print("  • Integrate with main orchestrator")
    print("  • Add more sophisticated strategy selectors")
    print("  • Implement parallel execution for multi-path exploration")
    print("  • Build comprehensive strategy library")
    print("  • Add visualization of solution paths")


if __name__ == "__main__":
    main()
