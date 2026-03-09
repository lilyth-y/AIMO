"""
Stage 1: Labeling & Semantic Decomposition
- Domain Classifier: Number Theory, Geometry, Algebra, Combinatorics
- Variable Extraction: Extract N, K, P, etc.
"""

import re
from typing import Dict, Any

class ProblemAnalyzer:
    """
    문제 분석기
    
    문제를 도메인으로 분류하고 변수를 추출합니다.
    향후 BERT 분류기나 LLM 프롬프트로 확장 가능합니다.
    """
    
    def __init__(self):
        """
        ProblemAnalyzer 초기화
        
        향후 BERT 분류기나 LLM 프롬프트를 로드할 수 있습니다.
        """
        # Placeholder for BERT classifier or LLM prompt
        pass

    def classify_domain(self, problem_text: str) -> str:
        """
        문제를 도메인으로 분류합니다.
        
        Args:
            problem_text: 문제 텍스트
        
        Returns:
            도메인 이름 (Geometry, Number Theory, Algebra, Combinatorics, 등)
        """
        problem_lower = problem_text.lower()
        
        # Geometry keywords
        geo_keywords = [
            'triangle', 'circle', 'angle', 'perpendicular', 'parallel',
            'tangent', 'area', 'perimeter', 'polygon', 'coordinate',
            'distance', 'midpoint', 'radius', 'diameter', 'chord',
            'rectangle', 'square', 'trapezoid', 'rhombus'
        ]
        
        # Number Theory keywords
        nt_keywords = [
            'mod', 'prime', 'gcd', 'lcm', 'divisible', 'integer',
            'factor', 'congruence', 'diophantine', 'modular',
            'remainder', 'divided by', 'divisor', 'multiple'
        ]
        
        # Algebra keywords
        alg_keywords = [
            'polynomial', 'equation', 'quadratic', 'cubic', 'root',
            'factor', 'expand', 'simplify', 'inequality', 'matrix'
        ]
        
        # Combinatorics keywords
        comb_keywords = [
            'permutation', 'combination', 'arrangement', 'count',
            'choose', 'binomial', 'pigeonhole', 'graph', 'tree',
            'ways to', 'how many ways', 'arrange', 'select'
        ]
        
        # Calculus keywords
        calc_keywords = [
            'limit', 'derivative', 'integral', 'series', 'converge',
            'diverge', 'taylor', 'optimization', 'f(x)', 'function',
            'differentiate', 'integrate', 'critical point'
        ]
        
        # Check each domain
        if any(kw in problem_lower for kw in geo_keywords):
            return "Geometry"
        elif any(kw in problem_lower for kw in nt_keywords):
            return "Number Theory"
        elif any(kw in problem_lower for kw in alg_keywords):
            return "Algebra"
        elif any(kw in problem_lower for kw in comb_keywords):
            return "Combinatorics"
        elif any(kw in problem_lower for kw in calc_keywords):
            return "Calculus"
        else:
            return "General"

    def extract_variables(self, problem_text: str) -> Dict[str, Any]:
        """
        Extracts variables and constraints from the problem text.
        """
        variables = {}
        # Simple regex to find N = ... or similar patterns
        # In a real scenario, this would use an LLM
        matches = re.findall(r'([A-Za-z])\s*=\s*(\d+)', problem_text)
        for var, val in matches:
            variables[var] = int(val)
        return variables

if __name__ == "__main__":
    analyzer = ProblemAnalyzer()
    text = "Find the number of integers N such that N < 1000 and N is prime."
    # Example usage (commented out for production)
    # print(f"Domain: {analyzer.classify_domain(text)}")
    # print(f"Variables: {analyzer.extract_variables(text)}")
