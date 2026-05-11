"""
Orchestrator Helper Functions
- 문제 분류 및 분석 헬퍼 함수
- 코드 수정 및 에러 처리 헬퍼 함수
- 검증 및 매핑 헬퍼 함수
"""

import re
from typing import Dict, Any, Optional

from .reasoning_utils import execution_output_requires_raw_return


def is_execution_error_output(s: Optional[str]) -> bool:
    """
    True if the string is executor/sandbox failure text that must not be verified as an answer.

    Delegates to ``execution_output_requires_raw_return`` so this stays aligned with
    ``extract_final_answer_from_output`` (same traceback / ``Error:`` / load-failure signals).
    """
    if not isinstance(s, str) or not s.strip():
        return False
    return execution_output_requires_raw_return(s)


def classify_problem(problem_text: str) -> str:
    """
    문제 유형을 분류합니다.
    
    Returns: 'computational', 'geometric', 'proof', 'complex', 'invalid'
    """
    result, _ = classify_problem_with_diagnosis(problem_text)
    return result


def classify_problem_with_diagnosis(problem_text: str) -> tuple:
    """
    문제 유형을 분류하고, 분류 근거를 함께 반환합니다.
    
    Returns: (classification: str, diagnosis: dict)
      - classification: 'computational', 'geometric', 'proof', 'complex', 'invalid'
      - diagnosis: {
          'input_text': str,
          'word_count': int,
          'has_math_symbols': bool,
          'found_math_symbols': list,
          'has_math_functions': bool,
          'found_math_functions': list,
          'has_math_keywords': bool,
          'found_math_keywords': list,
          'has_digits': bool,
          'is_conversational': bool,
          'found_conversational': list,
          'rejection_reason': str or None,
          'final_type': str
        }
    """
    problem_lower = problem_text.lower().strip()
    diagnosis = {
        'input_text': problem_text,
        'word_count': len(problem_lower.split()) if problem_lower else 0,
        'has_math_symbols': False,
        'found_math_symbols': [],
        'has_math_functions': False,
        'found_math_functions': [],
        'has_math_keywords': False,
        'found_math_keywords': [],
        'has_digits': False,
        'is_conversational': False,
        'found_conversational': [],
        'rejection_reason': None,
        'final_type': 'invalid',
    }

    if not problem_lower:
        diagnosis['rejection_reason'] = 'Empty input'
        return 'invalid', diagnosis

    # Basic math markers and keywords
    math_symbols = ['+', '-', '*', '/', '^', '=', '<', '>', '(', ')', '{', '}', '[', ']', 'π', 'θ', '∑', '∫', '∂']
    math_functions = ['sqrt', 'log', 'sin', 'cos', 'tan']
    math_keywords = [
        'sum', 'product', 'quotient', 'difference', 'multiply', 'divide', 'add', 'subtract', 'solve', 'calculate', 'find', 'equation', 'derivative', 'integral', 'limit', 'matrix', 'vector', 'probability', 'statistics', 'mean', 'median', 'mode', 'standard deviation',
        '합', '차', '곱', '몫', '나누기', '더하기', '빼기', '구하시오', '계산하시오', '풀이', '증명', '함수', '방정식', '부등식', '미분', '적분', '극한', '행렬', '벡터', '확률', '통계', '평균'
    ]

    found_syms = [sym for sym in math_symbols if sym in problem_text]
    found_fns = [fn for fn in math_functions if re.search(rf'\b{fn}\b', problem_lower)]
    found_kws = [kw for kw in math_keywords if re.search(rf'\b{kw}\b', problem_lower)]
    has_digit = any(char.isdigit() for char in problem_text)

    diagnosis['found_math_symbols'] = found_syms
    diagnosis['has_math_symbols'] = len(found_syms) > 0
    diagnosis['found_math_functions'] = found_fns
    diagnosis['has_math_functions'] = len(found_fns) > 0
    diagnosis['found_math_keywords'] = found_kws
    diagnosis['has_math_keywords'] = len(found_kws) > 0
    diagnosis['has_digits'] = has_digit

    has_math_marker = len(found_syms) > 0 or len(found_fns) > 0
    has_math_keyword = len(found_kws) > 0

    words = problem_lower.split()

    # 1. Very short inputs
    if len(words) <= 3:
        if not (has_math_marker or has_digit):
            diagnosis['rejection_reason'] = f'Input too short ({len(words)} words) and contains no math symbols or digits'
            diagnosis['final_type'] = 'invalid'
            return 'invalid', diagnosis
        conversation_keywords = ['hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye', 'how', 'who', 'what', 'where']
        found_conv = [kw for kw in conversation_keywords if kw in problem_lower]
        if found_conv and not has_math_marker:
            diagnosis['is_conversational'] = True
            diagnosis['found_conversational'] = found_conv
            diagnosis['rejection_reason'] = f'Conversational greeting/phrase detected ({found_conv}), no math symbols present'
            diagnosis['final_type'] = 'invalid'
            return 'invalid', diagnosis

    # 2. Heuristic for non-math context
    if not (has_math_marker or has_math_keyword):
        if not has_digit or len(words) < 10:
            if len(words) < 50:
                diagnosis['rejection_reason'] = (
                    f'No math symbols, functions, or keywords detected. '
                    f'Word count: {len(words)}. Digits: {has_digit}.'
                )
                diagnosis['final_type'] = 'invalid'
                return 'invalid', diagnosis

        common_conversational = ['how', 'what', 'why', 'who', 'where', 'weather', 'lunch', 'dinner', 'play', 'game', '안녕', '날씨', '점심', '저녁', '놀자', '게임', 'help']
        conv_hits = [w for w in words if any(ck in w for ck in common_conversational)]
        if conv_hits and len(conv_hits) / len(words) > 0.5:
            diagnosis['is_conversational'] = True
            diagnosis['found_conversational'] = conv_hits
            diagnosis['rejection_reason'] = f'High proportion of conversational words: {conv_hits}'
            diagnosis['final_type'] = 'invalid'
            return 'invalid', diagnosis

    # Geometric keywords
    geo_keywords = [
        'triangle', 'circle', 'angle', 'perpendicular', 'parallel',
        'tangent', 'area', 'perimeter', 'polygon', 'coordinate',
        'distance', 'midpoint', 'radius', 'diameter', 'chord'
    ]
    complex_indicators = [
        'prove that', 'show that', 'demonstrate', 'find all',
        'for what values', 'determine whether', 'if and only if'
    ]

    if any(keyword in problem_lower for keyword in geo_keywords):
        diagnosis['final_type'] = 'geometric'
        return 'geometric', diagnosis

    if any(indicator in problem_lower for indicator in complex_indicators):
        diagnosis['final_type'] = 'complex'
        return 'complex', diagnosis

    # Final sanity check
    conversation_keywords = ['hello', 'hi', 'hey', 'thanks', 'thank you', 'bye', 'goodbye', 'how are you', 'who are you', 'what is your name']
    found_conv_final = [kw for kw in conversation_keywords if kw in problem_lower]
    if found_conv_final and not (has_math_marker or (has_digit and len(words) > 5)):
        diagnosis['is_conversational'] = True
        diagnosis['found_conversational'] = found_conv_final
        diagnosis['rejection_reason'] = f'Conversational phrase detected ({found_conv_final}), insufficient math context'
        diagnosis['final_type'] = 'invalid'
        return 'invalid', diagnosis

    diagnosis['final_type'] = 'computational'
    return 'computational', diagnosis


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
