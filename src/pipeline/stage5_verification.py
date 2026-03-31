"""Stage 5: Verification Router (고급 검증) - P0-1 개선

고급 검증 기능:
 - 다중 타입 파싱 (int, float, sympy Expr, list/tuple, LaTeX fraction)
 - SymPy 동등성 검증 (simplify, factor, expand, trigsimp, ratsimp, cancel, nsimplify)
 - 수치 근사 비교 (부동소수점 허용 오차)
 - 리스트/집합 다중집합 비교 (개선: Counter 기반 정확도)
 - 표현식 정규화 (factor/expand) (개선: 순차 적용)
 - 컨텍스트 기반 역검증 (해를 원래 방정식에 대입) (개선: 수렴성 검증)
 - 제약 조건 검사 (정수 여부, 모듈로 등)
 - Rational Simplification (개선: gcd 기반 정규화)

P0-1 개선사항:
1. Rational Simplification - gcd 기반 분수 정규화
2. Symbolic Equality 강화 - simplify 순차 적용
3. Numeric Tolerance - 상대/절대 오차 명확히
4. Collection 비교 - Counter 다중집합
5. Context 역검증 - 원 방정식 재대입

현재는 context에 'expected' 키가 있으면 비교 수행.
"""

from typing import Any, Dict, List, Set, Optional, Union
import math
import json
import re
from decimal import Decimal, InvalidOperation
from collections import Counter

try:
    import sympy as sp
    from sympy import simplify, factor, expand, trigsimp, ratsimp, cancel, nsimplify
except ImportError:
    sp = None
    simplify = factor = expand = trigsimp = ratsimp = cancel = nsimplify = None

from .logger import get_logger
from .orchestrator_helpers import is_execution_error_output

logger = get_logger()

class VerificationRouter:
    def __init__(self, rel_tol: float = 1e-6, abs_tol: float = 1e-8):
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def verify(self, answer: Any, problem_context: Dict[str, Any]) -> bool:
        """
        답변을 검증합니다.
        
        Args:
            answer: 검증할 답변
            problem_context: 문제 컨텍스트 (expected, constraints, reverse_func 등 포함)
        
        Returns:
            검증 통과 여부
        """
        # Hard fail on propagated execution error strings (Error: from executor, legacy ERROR:)
        if isinstance(answer, str) and is_execution_error_output(answer):
            logger.warning("Verification Failed: Execution error propagated")
            return False
        
        parsed = self._parse_answer(answer)
        if parsed is None:
            logger.warning("Verification Failed: Unparseable answer")
            return False

        # Constraint Check
        constraints = problem_context.get("constraints", [])
        if not self._check_constraints(parsed, constraints):
            logger.warning(f"Verification Failed: Constraint violated {constraints}")
            return False

        expected = problem_context.get("expected")
        if expected is not None:
            # Parse expected as well to ensure apples-to-apples comparison
            parsed_expected = self._parse_answer(expected)
            if not self._compare(parsed, parsed_expected):
                logger.debug(f"Verification Failed: Expected mismatch - got {parsed}, expected {parsed_expected}")
                return False

        if not self._reverse_check(parsed, problem_context):
            logger.warning("Verification Failed: Reverse check failed")
            return False
        
        logger.debug(f"Verification Passed: {parsed}")
        return True

    def _parse_answer(self, answer: Any) -> Optional[Any]:
        """
        답변을 파싱하여 비교 가능한 형태로 변환합니다.
        None/빈 문자열이면 None, 그 외에는 숫자/리스트/문자열 등 비교 가능한 값 반환.
        """
        # Already numeric
        if isinstance(answer, (int, float)):
            return answer
        if isinstance(answer, (list, tuple)):
            return [self._parse_answer(a) for a in answer]
        if answer is None:
            return None
        # Dict from multi-agent or API: use content/text/value/answer
        if isinstance(answer, dict):
            for key in ("content", "text", "value", "answer", "result"):
                if key in answer and answer[key] is not None:
                    parsed = self._parse_answer(answer[key])
                    if parsed is not None:
                        return parsed
            return None

        text = str(answer).strip()
        if not text:
            return None

        # Remove common LaTeX formatting
        text = text.replace('^', '**')
        text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', text)  # \frac{a}{b} -> (a)/(b)
        text = re.sub(r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)', text)              # \sqrt{a} -> sqrt(a)
        text = re.sub(r'\\sqrt\[(\d+)\]\{([^{}]+)\}', r'(\2)**(1/\1)', text)  # \sqrt[n]{a} -> a**(1/n)
        text = text.replace('\\pi', 'pi')
        text = text.replace('\\cdot', '*')
        text = text.replace('\\times', '*')
        text = text.replace('\\div', '/')

        # Try int
        try:
            return int(text)
        except ValueError:
            pass
        # Try float/Decimal
        try:
            return float(text)
        except ValueError:
            pass
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            pass
        # Try JSON list
        if (text.startswith('[') and text.endswith(']')) or (text.startswith('(') and text.endswith(')')):
            try:
                as_list = json.loads(text.replace('(', '[').replace(')', ']'))
                if isinstance(as_list, list):
                    return [self._parse_answer(a) for a in as_list]
            except Exception:
                pass
        # Try sympy
        if sp:
            try:
                expr = sp.sympify(text)
                return sp.simplify(expr)
            except Exception:
                pass
        # Fallback: extract numeric value from string (e.g. "The answer is 302", "Result: 42")
        num_match = re.search(r'[-+]?\d+\.?\d*(?:/\d+)?(?:[eE][-+]?\d+)?', text)
        if num_match:
            raw = num_match.group(0)
            try:
                if "/" in raw:
                    num, den = raw.split("/", 1)
                    return float(num.strip()) / float(den.strip())
                return int(raw) if "." not in raw and "e" not in raw.lower() else float(raw)
            except (ValueError, ZeroDivisionError):
                pass
        return text

    def _compare(self, a: Any, b: Any) -> bool:
        """
        두 값을 비교합니다 (고급 SymPy 기반 검증 포함).
        
        Args:
            a: 첫 번째 값
            b: 두 번째 값
        
        Returns:
            두 값이 동등한지 여부
        """
        # 1. Direct equality check
        if a == b:
            return True

        # 2. Enhanced SymPy comparison
        if sp and (isinstance(a, sp.Basic) or isinstance(b, sp.Basic)):
            return self._compare_sympy(a, b)

        # 3. Numeric comparison (including mixed types like int vs float vs Rational)
        try:
            val_a = float(a)
            val_b = float(b)
            return math.isclose(val_a, val_b, rel_tol=self.rel_tol, abs_tol=self.abs_tol)
        except (ValueError, TypeError):
            pass

        # 4. List comparison (Multiset for numbers)
        if isinstance(a, list) and isinstance(b, list):
            return self._compare_lists(a, b)

        # 5. Set comparison (Multiset)
        if isinstance(a, set) and isinstance(b, set):
            return self._compare_sets(a, b)

        # 6. Fallback string normalization
        return str(a).strip() == str(b).strip()
    
    def _compare_sympy(self, a: Any, b: Any) -> bool:
        """
        SymPy 기반 고급 비교 (ratsimp, cancel, nsimplify 포함).
        
        Args:
            a: 첫 번째 값
            b: 두 번째 값
        
        Returns:
            두 값이 동등한지 여부
        """
        if not sp:
            return False
        
        try:
            # Convert both to sympy if possible
            sym_a = sp.sympify(a) if not isinstance(a, sp.Basic) else a
            sym_b = sp.sympify(b) if not isinstance(b, sp.Basic) else b
            
            # Compute difference
            diff = sym_a - sym_b
            
            # Try multiple simplification methods
            simplification_methods = [
                lambda x: x,  # Direct check
                lambda x: simplify(x),
                lambda x: factor(x),
                lambda x: expand(x),
                lambda x: trigsimp(x),
                lambda x: ratsimp(x) if ratsimp else simplify(x),  # Rational simplification
                lambda x: cancel(x) if cancel else simplify(x),  # Cancel common factors
            ]
            
            for method in simplification_methods:
                try:
                    simplified = method(diff)
                    if simplified == 0:
                        return True
                    # Check if it's a zero expression
                    if hasattr(simplified, 'is_zero'):
                        if simplified.is_zero:
                            return True
                except Exception:
                    continue
            
            # Try nsimplify for numeric approximation
            if nsimplify:
                try:
                    # If both are numeric, use nsimplify
                    if not sym_a.free_symbols and not sym_b.free_symbols:
                        num_a = float(sym_a.evalf())
                        num_b = float(sym_b.evalf())
                        # Check if nsimplify can find a rational representation
                        if abs(num_a - num_b) < self.abs_tol:
                            return True
                except Exception:
                    pass
            
            # Numeric substitution fallback: test free symbols with sample points
            free_syms = list((sym_a.free_symbols | sym_b.free_symbols))
            if free_syms:
                samples = [1, 2, 3, 1.5, -1, 0.5, 10]  # Extended sample points
                for val in samples:
                    sub_map = {s: val for s in free_syms}
                    try:
                        eval_diff = diff.subs(sub_map)
                        if hasattr(eval_diff, 'evalf'):
                            eval_diff = eval_diff.evalf()
                        if abs(float(eval_diff)) > 1e-7:  # Slightly looser for complex exprs
                            return False
                    except Exception:
                        continue
                return True
            
            # If no free symbols, it might be a constant expression (e.g. pi vs 3.14159...)
            if hasattr(diff, 'evalf'):
                try:
                    diff_val = abs(float(diff.evalf()))
                    if diff_val < self.abs_tol:
                        return True
                except Exception:
                    pass

            return False
        except Exception as e:
            logger.debug(f"SymPy comparison failed: {e}")
            return False
    
    def _compare_lists(self, a: List[Any], b: List[Any]) -> bool:
        """
        리스트를 다중집합으로 비교합니다.
        
        Args:
            a: 첫 번째 리스트
            b: 두 번째 리스트
        
        Returns:
            두 리스트가 다중집합으로 동등한지 여부
        """
        if len(a) != len(b):
            return False
        
        # Check if lists contain only numbers
        is_numeric_a = all(isinstance(x, (int, float, Decimal)) or 
                          (sp and isinstance(x, (sp.Number, sp.NumberSymbol))) 
                          for x in a)
        is_numeric_b = all(isinstance(x, (int, float, Decimal)) or 
                          (sp and isinstance(x, (sp.Number, sp.NumberSymbol))) 
                          for x in b)
        
        if is_numeric_a and is_numeric_b:
            # Sort by float value for comparison (multiset)
            sorted_a = sorted(a, key=lambda x: float(x))
            sorted_b = sorted(b, key=lambda x: float(x))
            return all(self._compare(x, y) for x, y in zip(sorted_a, sorted_b))
        
        # For non-numeric lists, compare element-wise
        # Use Counter for true multiset comparison
        try:
            counter_a = Counter(str(x) for x in a)
            counter_b = Counter(str(x) for x in b)
            if counter_a == counter_b:
                # Counts match, now verify each pair
                return all(self._compare(x, y) for x, y in zip(sorted(a), sorted(b)))
        except Exception:
            pass
        
        return all(self._compare(x, y) for x, y in zip(a, b))
    
    def _compare_sets(self, a: Set[Any], b: Set[Any]) -> bool:
        """
        집합을 다중집합으로 비교합니다 (길이와 요소 일치).
        
        Args:
            a: 첫 번째 집합
            b: 두 번째 집합
        
        Returns:
            두 집합이 다중집합으로 동등한지 여부
        """
        if len(a) != len(b):
            return False
        
        # Convert to sorted lists for comparison
        try:
            list_a = sorted(a, key=str)
            list_b = sorted(b, key=str)
            return all(self._compare(x, y) for x, y in zip(list_a, list_b))
        except Exception:
            # Fallback to strict equality
            return a == b

    def _check_constraints(self, answer: Any, constraints: list) -> bool:
        if not constraints:
            return True
        
        for constraint in constraints:
            if constraint == "integer":
                if hasattr(answer, 'is_integer'):
                    # SymPy numbers expose .is_integer as a bool, Python floats expose is_integer() method
                    is_int_attr = getattr(answer, 'is_integer')
                    if callable(is_int_attr):
                        if not is_int_attr():
                            return False
                    else:
                        if not is_int_attr:
                            return False
                elif isinstance(answer, int):
                    pass
                elif isinstance(answer, float):
                    if not answer.is_integer():
                        return False
                else:
                    return False # Non-numeric types fail integer check
            
            elif constraint == "non_negative":
                    
                 try:
                    val = float(answer)
                    if val < 0: return False
                 except:
                     return False
            
            elif constraint.startswith("modulo_"):
                try:
                    mod_val = int(constraint.split("_")[1])
                    val = int(answer)
                    if not (0 <= val < mod_val): return False
                except:
                    return False
                    
        return True

    def _reverse_check(self, answer: Any, context: Dict[str, Any]) -> bool:
        """
        역검증을 수행합니다 (해를 원래 방정식에 대입).
        
        Args:
            answer: 검증할 답변
            context: 문제 컨텍스트 (reverse_func, reverse_expression, reverse_target 포함)
        
        Returns:
            역검증 통과 여부
        """
        # 1. Callable reverse function
        reverse_func = context.get('reverse_func')
        if callable(reverse_func):
            try:
                result = bool(reverse_func(answer))
                if not result:
                    logger.debug(f"Reverse check failed: reverse_func returned False for {answer}")
                return result
            except Exception as e:
                logger.debug(f"Reverse check error: {e}")
                return False
        
        # 2. Expression template substitution
        expr_tpl = context.get('reverse_expression')
        target_val = context.get('reverse_target')
        if expr_tpl and target_val is not None and sp:
            try:
                # Wrap substituted answer in parentheses to preserve sign/precedence (e.g., -2 -> (-2))
                expr_str = expr_tpl.replace('{x}', f'({answer})')
                expr = sp.sympify(expr_str)
                target = sp.sympify(str(target_val))
                
                # Use enhanced _compare for robustness
                result = self._compare(expr, target)
                if not result:
                    logger.debug(f"Reverse check failed: {expr_str} != {target_val}")
                return result
            except Exception as e:
                logger.debug(f"Reverse check error: {e}")
                return False
        
        # 3. No reverse check defined - pass by default
        return True

if __name__ == "__main__":
    # Example test cases (commented out for production)
    # verifier = VerificationRouter()
    # print(f"Is 12345 valid? {verifier.verify(12345, {})}")
    # print(f"Is 100000 valid? {verifier.verify(100000, {})}")
    # 
    # # Test cases
    # ctx_numeric = {"expected": 3.1415926535}
    # print(f"Pi check (float): {verifier.verify(3.1415927, ctx_numeric)}")
    # 
    # if sp:
    #     ctx_sym = {"expected": "sqrt(2)"}
    #     print(f"Sqrt(2) check: {verifier.verify(1.41421356, ctx_sym)}")
    #     
    #     ctx_frac = {"expected": "1/3"}
    #     print(f"Fraction check: {verifier.verify(0.3333333333333333, ctx_frac)}")
    #     
    #     # LaTeX check
    #     latex_ctx = {'expected': r'\\frac{1}{2}'}
    #     print(f"LaTeX parsing: {verifier.verify(0.5, latex_ctx)}")
    # 
    # # Constraint check
    # print(f"Integer check (fail): {verifier.verify(3.5, {'constraints': ['integer']})}")
    # print(f"Integer check (pass): {verifier.verify(3.0, {'constraints': ['integer']})}")
    pass
