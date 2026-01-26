"""Feature Extraction for Strategy Selection

Generates lightweight, numeric/categorical features from a problem statement and
current pipeline context to support learned strategy ordering (bandit / classifier).

Design principles:
 - Pure functions, JSON-serializable output
 - SymPy optional (graceful degradation)
 - Cheap to compute (avoid heavy model calls)
 - Backwards compatible: absence of features should not break logging
"""

from __future__ import annotations
from typing import Dict, Any
import re

try:
    import sympy as sp  # optional
except ImportError:
    sp = None

MATH_KEYWORDS = {
    'geometry': [
        'triangle','circle','angle','perpendicular','parallel','tangent','radius','diameter','chord','polygon','midpoint','area','perimeter'
    ],
    'number_theory': [
        'prime','gcd','lcm','mod','divisible','integer','factor','congruence','diophantine'
    ],
    'algebra': [
        'polynomial','factor','expand','root','quadratic','cubic','equation','system','simplify'
    ],
    'calculus': [
        'limit','derivative','integral','series','converge','diverge'
    ],
    'puzzle': [
        'puzzle','퍼즐','constraint','제약','logic','논리','satisfy','만족','condition','조건',
        'arrange','배치','permutation','순열','combination','조합','grid','격자','sudoku','스도쿠',
        'crossword','크로스워드','riddle','수수께끼','pattern','패턴','rule','규칙'
    ]
}

SYMBOLS = ['+','-','*','/','^','=','<','>']

def count_occurrences(text: str, tokens: list[str]) -> int:
    tl = text.lower()
    return sum(tl.count(tok) for tok in tokens)

def operator_diversity(text: str) -> int:
    return sum(1 for s in SYMBOLS if s in text)

def keyword_presence(text: str) -> Dict[str,int]:
    tl = text.lower()
    return {group: sum(1 for kw in kws if kw in tl) for group, kws in MATH_KEYWORDS.items()}

def clause_count(text: str) -> int:
    return text.count(',') + text.count(';')

def char_classes(text: str) -> Dict[str,int]:
    return {
        'digits': sum(ch.isdigit() for ch in text),
        'letters': sum(ch.isalpha() for ch in text),
        'whitespace': sum(ch.isspace() for ch in text),
    }

def expression_density(text: str) -> int:
    # crude: count parentheses and math symbols
    return sum(text.count(c) for c in ['(',')']) + operator_diversity(text)

def extract_features(problem_text: str, complexity_score: int | None = None) -> Dict[str, Any]:
    """Return feature dict for logging & strategy selection.
    complexity_score: provided externally (assess_complexity) for consistency.
    """
    features: Dict[str, Any] = {}
    features['length'] = len(problem_text)
    features['lines'] = problem_text.count('\n') + 1
    features['complexity_score'] = complexity_score
    features['operator_diversity'] = operator_diversity(problem_text)
    features['clause_count'] = clause_count(problem_text)
    features['expr_density'] = expression_density(problem_text)
    features.update({f'kw_{k}': v for k, v in keyword_presence(problem_text).items()})
    features.update(char_classes(problem_text))
    # domain hints
    dominant_domain = max(keyword_presence(problem_text).items(), key=lambda x: x[1])[0] if any(keyword_presence(problem_text).values()) else 'general'
    features['dominant_domain'] = dominant_domain
    return features

def rapid_intuition_phase(problem_text: str) -> tuple[str, str]:
    """
    Rapid intuition phase: classify problem type intuitively (diffusion-style recognition).

    Computes lightweight heuristics to immediately suggest problem domain and preferred strategy.

    Returns: (problem_type, preferred_strategy)
        problem_type: "geometry", "number_theory", "algebra", "calculus", "misc"
        preferred_strategy: "Theoretician", "Simulator", "Hybrid", or None
    """
    tl = problem_text.lower()

    # Keyword-driven classification
    if any(kw in tl for kw in MATH_KEYWORDS['puzzle']):
        return "puzzle", "Simulator"  # Puzzles often need constraint satisfaction or brute force
    
    if any(kw in tl for kw in MATH_KEYWORDS['geometry']):
        return "geometry", "Theoretician"  # Symbolic math preferred for geometry

    if any(kw in tl for kw in MATH_KEYWORDS['number_theory']):
        return "number_theory", "Simulator"  # Often needs computation

    if any(kw in tl for kw in MATH_KEYWORDS['algebra']):
        return "algebra", "Simulator"  # Equation solving via computation

    if any(kw in tl for kw in MATH_KEYWORDS['calculus']):
        return "calculus", "Theoretician"  # Symbolic integration/derivation

    # Fallback: general problems → multi-path
    if len(tl.split()) < 50:  # Short problems likely arithmetic/geometry
        if any(sym in problem_text for sym in SYMBOLS[:3]):  # ±* present
            return "arithmetic", "Simulator"
        else:
            return "general", "Hybrid"

    return "misc", None  # Unknown, use full pipeline

__all__ = ['extract_features', 'rapid_intuition_phase']
