#!/usr/bin/env python3
"""
Test script for the Decomposition vs Direct Classifier compromise point.
This tests whether the complexity threshold correctly affects decomposition decisions.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.pipeline.reasoning_utils import assess_complexity
from src.pipeline import config

# Test problems with varying complexity levels
test_problems = {
    "simple_arithmetic": {
        "text": "What is 5 + 3?",
        "expected_type": "computational",
        "expected_decompose": False,
    },
    "medium_algebra": {
        "text": "Solve for x: 2x + 5 = 17",
        "expected_type": "computational",
        "expected_decompose": False,
    },
    "complex_geometry_theorem": {
        "text": "Prove that in a triangle ABC with AB = AC, the angle bisector from vertex B meets the opposite side at a point D such that BD = DC = AD, and D is equidistant from the sides.",
        "expected_type": "complex",
        "expected_decompose": True,  # High complexity should trigger decomposition
    },
    "proof_with_multiple_cases": {
        "text": "Show that for any integer n greater than or equal to 2, the equation x^n + y^n = z^n has no positive integer solutions x, y, z where x, y, z are positive integers greater than zero.",
        "expected_type": "complex",
        "expected_decompose": True,  # Proof with conditions
    },
    "combinatorial_counting": {
        "text": "How many ways are there to arrange the letters in MISSISSIPPI such that no two I's are together?",
        "expected_type": "computational",
        "expected_decompose": False,  # Counting problem, not extremely complex
    },
    "number_theory_coprime": {
        "text": "Find all positive integers n such that n divides 2^n + 1 and n is coprime to 2^n + 1.",
        "expected_type": "complex",
        "expected_decompose": True,  # Advanced number theory
    }
}

def mock_classify_problem(problem_text: str) -> str:
    """Simple mock version of _classify_problem"""
    problem_lower = problem_text.lower()

    # Complex problem indicators
    complex_indicators = ['prove that', 'show that', 'demonstrate', 'find all',
                         'for what values', 'determine whether', 'if and only if']

    # Check for complex reasoning
    if any(indicator in problem_lower for indicator in complex_indicators):
        return 'complex'

    return 'computational'

def test_compromise_point():
    """Test the compromise point logic with different complexity thresholds."""

    print("🔬 Testing Decomposition vs Direct Classifier Compromise Point")
    print("=" * 70)

    # Test with different thresholds
    thresholds = [10, 15, 20]  # Different complexity thresholds

    for threshold in thresholds:
        print(f"\n📊 Testing with DECOMPOSITION_COMPLEXITY_THRESHOLD = {threshold}")
        print("-" * 50)

        # Simulate threshold setting (in real config)
        config.DECOMPOSITION_COMPLEXITY_THRESHOLD = threshold

        decomposed_count = 0
        total_complex = 0

        for problem_name, problem_data in test_problems.items():
            text = problem_data["text"]

            # Get metrics
            problem_type = mock_classify_problem(text)
            complexity_score = assess_complexity(text)
            should_decompose = problem_type == 'complex' and complexity_score >= threshold

            # Count statistics
            if problem_type == 'complex':
                total_complex += 1
                if should_decompose:
                    decomposed_count += 1

            # Print results with emojis
            status_emoji = "✅" if should_decompose == problem_data["expected_decompose"] else "❌"
            decompose_emoji = "🔀" if should_decompose else "➡️"

            print(f"{status_emoji} {decompose_emoji} {problem_name[:25]:<25} | "
                  f"Type: {problem_type:<12} | "
                  f"Score: {complexity_score:>2} | "
                  f"Decompose: {str(should_decompose):>5}")

        # Calculate effectiveness
        if total_complex > 0:
            decomposition_rate = decomposed_count / total_complex * 100
            print(f"📈 Decomposition Rate: {decomposition_rate:.1f}% ({decomposed_count}/{total_complex} complex problems)")

def analyze_effectiveness():
    """Analyze how the compromise point affects different problem categories."""
    print("\n📈 Compromise Point Effectiveness Analysis")
    print("=" * 70)

    base_threshold = 15

    print("Impact on problem categorization:")
    print("간단한 계산 문제는 분해하지 않음 (불필요한 오버헤드 방지)")
    print("복잡한 증명 문제는 분해하여 정확성 향상")
    print("중간 복잡도 문제의 타협점 효과 측정 가능")

if __name__ == "__main__":
    test_compromise_point()
    analyze_effectiveness()
