"""
Stage 1: Labeling & Semantic Decomposition
- Domain Classifier: Number Theory, Geometry, Algebra, Combinatorics
- Variable Extraction: Extract N, K, P, etc.
"""

import json
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
        
        # Number Theory keywords (avoid bare 'factor' — conflicts with polynomial factoring)
        nt_keywords = [
            'mod', 'prime', 'gcd', 'lcm', 'divisible', 'integer',
            'congruence', 'diophantine', 'modular',
            'remainder', 'divided by', 'divisor', 'multiple'
        ]
        
        # Algebra keywords
        alg_keywords = [
            'polynomial', 'equation', 'quadratic', 'cubic', 'root',
            'factor', 'expand', 'simplify', 'inequality', 'matrix', 'system'
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
        
        # Check each domain (polynomial factoring is algebra, not NT "factorization")
        if any(kw in problem_lower for kw in geo_keywords):
            return "Geometry"
        if 'polynomial' in problem_lower:
            return "Algebra"
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
        Supports: N = 10, n=10, N= 10, and "let N be 10" / "N be 10" style.
        """
        variables = {}
        # X = 123 or x=123, N= 10 (flexible spaces); 단일 문자는 대문자로 통일 (라우터가 N 사용)
        for var, val in re.findall(r'([A-Za-z])\s*=\s*(\d+)', problem_text):
            key = var.upper() if len(var) == 1 else var
            variables[key] = int(val)
        # "let N be 10" or "N be 10"
        for var, val in re.findall(r'(?:let\s+)?([A-Za-z])\s+be\s+(\d+)', problem_text, re.IGNORECASE):
            key = var.upper() if len(var) == 1 else var
            if key not in variables:
                variables[key] = int(val)
        return variables

    def classify_with_llm(self, problem_text: str) -> Dict[str, Any]:
        """
        Optional LLM-based Stage1 classifier.
        Returns lightweight structured hints and falls back gracefully.
        """
        try:
            from .vertex_inference import is_vertex_configured, generate_vertex
            from .orchestrator_helpers import classify_problem, is_execution_error_output
            from .reasoning_utils import assess_complexity
        except Exception:
            return {}

        if not is_vertex_configured():
            return {}

        prompt = (
            "You are a strict JSON classifier for math problems.\n"
            "Return ONLY JSON with keys: problem_type, complexity_score.\n"
            "problem_type must be one of: computational, geometric, proof, complex.\n"
            "complexity_score must be an integer from 0 to 30.\n"
            f"Problem:\n{problem_text}\n"
        )
        raw = generate_vertex(prompt, max_output_tokens=120)
        if not raw or is_execution_error_output(raw):
            return {}

        try:
            text = raw.strip()
            if "```" in text:
                text = text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(text)
            problem_type = str(parsed.get("problem_type", "")).strip().lower()
            complexity_score = int(parsed.get("complexity_score", -1))
            if problem_type not in {"computational", "geometric", "proof", "complex"}:
                return {}
            if complexity_score < 0 or complexity_score > 30:
                return {}
            return {
                "problem_type": problem_type,
                "complexity_score": complexity_score,
            }
        except Exception:
            # If model output is malformed, ignore and keep deterministic heuristics.
            return {
                "problem_type": classify_problem(problem_text),
                "complexity_score": assess_complexity(problem_text),
            }

if __name__ == "__main__":
    analyzer = ProblemAnalyzer()
    text = "Find the number of integers N such that N < 1000 and N is prime."
    # Example usage (commented out for production)
    # print(f"Domain: {analyzer.classify_domain(text)}")
    # print(f"Variables: {analyzer.extract_variables(text)}")
