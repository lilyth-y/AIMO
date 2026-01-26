"""Stage 5: Verification Router (확장)
기능:
 - 다중 타입 파싱 (int, float, sympy Expr, list/tuple, LaTeX fraction)
 - SymPy 동등성(trigsimp, factor, expand) / 수치 근사 비교
 - Reverse check 훅 (context 기반 확장 여지)
 - 제약 조건 검사 (정수 여부 등)
현재는 context에 'expected' 키가 있으면 비교 수행.
"""

from typing import Any, Dict
import math
import json
import re
from decimal import Decimal, InvalidOperation

try:
    import sympy as sp
except ImportError:
    sp = None

class VerificationRouter:
    def __init__(self, rel_tol: float = 1e-6, abs_tol: float = 1e-8):
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def verify(self, answer: Any, problem_context: Dict[str, Any]) -> bool:
        # Hard fail on propagated execution error strings
        if isinstance(answer, str) and answer.strip().startswith('ERROR:'):
            print("   -> X Verification Failed: Execution error propagated")
            return False
        parsed = self._parse_answer(answer)
        if parsed is None:
            print("   -> X Verification Failed: Unparseable answer")
            return False

        # Constraint Check
        constraints = problem_context.get("constraints", [])
        if not self._check_constraints(parsed, constraints):
            print(f"   -> X Verification Failed: Constraint violated {constraints}")
            return False

        expected = problem_context.get("expected")
        if expected is not None:
            # Parse expected as well to ensure apples-to-apples comparison
            parsed_expected = self._parse_answer(expected)
            if not self._compare(parsed, parsed_expected):
                print("   -> X Verification Failed: Expected mismatch")
                return False

        if not self._reverse_check(parsed, problem_context):
            print("   -> X Verification Failed: Reverse check failed")
            return False
        return True

    def _parse_answer(self, answer: Any):
        # Already numeric
        if isinstance(answer, (int, float)): return answer
        if isinstance(answer, (list, tuple)): return [self._parse_answer(a) for a in answer]
        if answer is None: return None
        text = str(answer).strip()
        if not text:
            return None
        
        # Remove common LaTeX formatting
        text = text.replace('^', '**')
        text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', text) # \frac{a}{b} -> (a)/(b)
        text = re.sub(r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)', text)             # \sqrt{a} -> sqrt(a)
        text = text.replace('\\pi', 'pi')

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
                return text  # fallback raw string
        return text

    def _compare(self, a: Any, b: Any) -> bool:
        # 1. Direct equality check
        if a == b: return True

        # 2. SymPy comparison
        if sp and (isinstance(a, sp.Basic) or isinstance(b, sp.Basic)):
            try:
                # Convert both to sympy if possible
                sym_a = sp.sympify(a) if not isinstance(a, sp.Basic) else a
                sym_b = sp.sympify(b) if not isinstance(b, sp.Basic) else b
                
                diff = sp.simplify(sym_a - sym_b)
                if diff == 0 or sp.factor(diff) == 0 or sp.expand(diff) == 0 or sp.trigsimp(diff) == 0:
                    return True
                
                # Numeric substitution fallback: test free symbols with sample points
                free_syms = list((sym_a.free_symbols | sym_b.free_symbols))
                if free_syms:
                    samples = [1, 2, 3, 1.5] # Added float sample
                    for val in samples:
                        sub_map = {s: val for s in free_syms}
                        try:
                            eval_diff = diff.subs(sub_map)
                            if hasattr(eval_diff, 'evalf'):
                                eval_diff = eval_diff.evalf()
                            if abs(float(eval_diff)) > 1e-7: # Slightly looser for complex exprs
                                return False
                        except Exception:
                            return False
                    return True
                
                # If no free symbols, it might be a constant expression (e.g. pi vs 3.14159...)
                if hasattr(diff, 'evalf'):
                     if abs(float(diff.evalf())) < self.abs_tol:
                         return True

                return False
            except Exception:
                pass # Fall through to other methods

        # 3. Numeric comparison (including mixed types like int vs float vs Rational)
        try:
            val_a = float(a)
            val_b = float(b)
            return math.isclose(val_a, val_b, rel_tol=self.rel_tol, abs_tol=self.abs_tol)
        except (ValueError, TypeError):
            pass

        # 4. List comparison (Multiset for numbers)
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            # Check if lists contain only numbers
            is_numeric_a = all(isinstance(x, (int, float, Decimal)) or (sp and isinstance(x, (sp.Number, sp.NumberSymbol))) for x in a)
            is_numeric_b = all(isinstance(x, (int, float, Decimal)) or (sp and isinstance(x, (sp.Number, sp.NumberSymbol))) for x in b)
            
            if is_numeric_a and is_numeric_b:
                # Sort by float value for comparison
                sorted_a = sorted(a, key=lambda x: float(x))
                sorted_b = sorted(b, key=lambda x: float(x))
                return all(self._compare(x, y) for x, y in zip(sorted_a, sorted_b))
            
            return all(self._compare(x, y) for x, y in zip(a, b))

        # 5. Set comparison
        if isinstance(a, set) and isinstance(b, set):
            if len(a) != len(b): return False
            # Set equality is hard with fuzzy matching, convert to sorted list logic?
            # For now, strict equality
            return a == b

        # 6. Fallback string normalization
        return str(a).strip() == str(b).strip()

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
        reverse_func = context.get('reverse_func')
        if callable(reverse_func):
            try:
                return bool(reverse_func(answer))
            except Exception:
                return False
        expr_tpl = context.get('reverse_expression')
        target_val = context.get('reverse_target')
        if expr_tpl and target_val is not None and sp:
            try:
                # Wrap substituted answer in parentheses to preserve sign/precedence (e.g., -2 -> (-2))
                expr = sp.sympify(expr_tpl.replace('{x}', f'({answer})'))
                target = sp.sympify(str(target_val))
                return self._compare(expr, target) # Use _compare instead of simplify(..)==0 for robustness
            except Exception:
                return False
        return True

if __name__ == "__main__":
    verifier = VerificationRouter()
    print(f"Is 12345 valid? {verifier.verify(12345, {})}")
    print(f"Is 100000 valid? {verifier.verify(100000, {})}")
    
    # Test cases
    ctx_numeric = {"expected": 3.1415926535}
    print(f"Pi check (float): {verifier.verify(3.1415927, ctx_numeric)}") # Should be true within default tol
    
    if sp:
        ctx_sym = {"expected": "sqrt(2)"}
        print(f"Sqrt(2) check: {verifier.verify(1.41421356, ctx_sym)}") # Should be true
        
        ctx_frac = {"expected": "1/3"}
        print(f"Fraction check: {verifier.verify(0.3333333333333333, ctx_frac)}")
        
        # LaTeX check
        latex_ctx = {'expected': r'\\frac{1}{2}'}
        print(f"LaTeX parsing: {verifier.verify(0.5, latex_ctx)}")

    # Constraint check
    print(f"Integer check (fail): {verifier.verify(3.5, {'constraints': ['integer']})}")
    print(f"Integer check (pass): {verifier.verify(3.0, {'constraints': ['integer']})}")
