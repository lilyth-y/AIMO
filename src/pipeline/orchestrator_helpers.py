"""
Orchestrator Helper Functions
- 문제 분류 및 분석 헬퍼 함수
- 코드 수정 및 에러 처리 헬퍼 함수
- 검증 및 매핑 헬퍼 함수
"""

import re
from typing import Dict, Any, Optional


def is_execution_error_output(s: Optional[str]) -> bool:
    """
    True if the string is a sandbox/executor failure line (e.g. ``Error: Timeout`` from
    stage4, or legacy ``ERROR:``). Case-insensitive on the ``error:`` prefix.
    """
    if not isinstance(s, str) or not s.strip():
        return False
    return s.strip().lower().startswith("error:")


def classify_problem(problem_text: str) -> str:
    """
    문제 유형을 분류합니다.
    
    Returns: 'computational', 'geometric', 'proof', 'complex'
    """
    problem_lower = problem_text.lower()
    
    # Geometric keywords
    geo_keywords = [
        'triangle', 'circle', 'angle', 'perpendicular', 'parallel',
        'tangent', 'area', 'perimeter', 'polygon', 'coordinate',
        'distance', 'midpoint', 'radius', 'diameter', 'chord'
    ]
    
    # Complex problem indicators
    complex_indicators = [
        'prove that', 'show that', 'demonstrate', 'find all',
        'for what values', 'determine whether', 'if and only if'
    ]
    
    # Check for geometry
    if any(keyword in problem_lower for keyword in geo_keywords):
        return 'geometric'
    
    # Check for complex reasoning
    if any(indicator in problem_lower for indicator in complex_indicators):
        return 'complex'
    
    # Default to computational
    return 'computational'


def inject_reverse_check(problem_text: str, variables: Dict[str, Any]) -> None:
    """
    간단한 산술 문제에 대한 역검증 훅을 주입합니다.
    
    Args:
        problem_text: 문제 텍스트
        variables: 변수 딕셔너리 (수정됨)
    """
    pat = re.compile(r"(what is|compute|evaluate)\s+([0-9]+)\s*([+\-*/])\s*([0-9]+)", re.IGNORECASE)
    m = pat.search(problem_text)
    
    if not m:
        return
    
    a = int(m.group(2))
    op = m.group(3)
    b = int(m.group(4))
    
    def rev(ans: Any) -> bool:
        try:
            val = int(str(ans).strip())
        except Exception:
            return False
        
        if op == '+':
            return a + b == val
        if op == '-':
            return a - b == val
        if op == '*':
            return a * b == val
        if op == '/':
            return b != 0 and a / b == val
        
        return False
    
    variables['reverse_func'] = rev


def build_fix_code_prompt(original_code: str, error_msg: str) -> Optional[str]:
    """
    실행 오류 메시지에 맞는 수정 요청 프롬프트를 만듭니다.
    NameError/AttributeError/SyntaxError 등에 대한 힌트를 포함합니다.
    
    Returns:
        LLM에 넘길 프롬프트 문자열 또는 None
    """
    if not original_code or not error_msg or "Error:" not in error_msg:
        return None
    hint = ""
    if "NameError" in error_msg or "name '" in error_msg and "is not defined" in error_msg:
        hint = (
            "NameError: Define the missing variable before use, or add the missing import "
            "(e.g. 'import sympy' or 'from sympy import symbols, solve, simplify'). "
            "If the error says 'sympy' is not defined, add: import sympy (or from sympy import ...). "
        )
    elif "AttributeError" in error_msg or "has no attribute" in error_msg:
        hint = (
            "AttributeError: Check object type. For SymPy expressions use .subs(), .simplify(); "
            "for Python float/int do not use .subs(). Use sympify() to convert to SymPy if needed. "
        )
    elif "SyntaxError" in error_msg or "Syntax error" in error_msg:
        hint = (
            "SyntaxError: Fix the reported line (e.g. matching parentheses in f-strings, "
            "missing colon, or invalid syntax). Output only valid Python code. "
        )
    elif "Timeout" in error_msg or "MemoryLimitExceeded" in error_msg:
        hint = "Optimize: avoid huge lists, use iteration or sampling, cap large N. "
    prompt = (
        "The following Python code raised an error. Fix it and output only the corrected code (no explanation).\n"
        f"Error: {error_msg}\n"
        f"{hint}\n"
        "Code:\n"
        f"{original_code}\n\n"
        "Corrected code:"
    )
    return prompt


def attempt_code_fix(original_code: str, error_msg: str) -> Optional[str]:
    """
    실행 오류를 분석하여 코드를 수정 시도합니다.
    휴리스틱으로 수정할 수 없으면 None 반환 (호출자가 build_fix_code_prompt로 LLM 재생성 가능).
    """
    if "Timeout" in error_msg or "SyntaxError" in error_msg or "Syntax error" in error_msg:
        return None  # LLM 기반 수정으로 처리
    if "NameError" in error_msg or "AttributeError" in error_msg:
        return None  # LLM 기반 수정으로 처리
    return None


def map_reconciliation_status_to_refine_error(rec_status: str) -> str:
    """
    Reconciliation 상태를 refine 프롬프트의 에러 타입으로 매핑합니다.
    
    Args:
        rec_status: Reconciliation 상태
    
    Returns:
        refine 프롬프트에서 사용할 에러 타입
    """
    mapping = {
        'MISMATCH_ARITHMETIC': 'arithmetic',
        'MISMATCH_LOGIC': 'logic',
        'ERROR_PARSING': 'other',
        'MISMATCH_FORMAT_DIFF': 'format'
    }
    
    return mapping.get(rec_status, 'other')


def solve_result_verification_fields(variables: Optional[Dict[str, Any]], verified: bool) -> Dict[str, Any]:
    """
    Returned with solve_problem so callers know whether ``verified`` was checked
    against a reference (``variables['expected']``) or only internal pipeline checks.
    Numina eval passes ``variables={}`` → verification_includes_reference_answer is False.
    """
    v = variables or {}
    return {
        "verified": verified,
        "verification_includes_reference_answer": v.get("expected") is not None,
    }
