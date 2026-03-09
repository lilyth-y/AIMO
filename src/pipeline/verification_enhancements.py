"""
P0-1: Advanced Verification Enhancement

목표:
- Rational Simplification
- Symbolic Equality 강화
- Context 역검증 개선
- 99곡선 대수 문제 90%+ 정확도

위치: src/pipeline/verification_enhancements.py
"""

from typing import Any, Optional, Tuple, TYPE_CHECKING, List, Dict, Callable
from math import gcd

from .logger import get_logger

logger = get_logger()

# SymPy availability flag
_sympy_available = False

if TYPE_CHECKING:
    import sympy as sp
else:
    try:
        import sympy as sp
        _sympy_available = True
    except ImportError:
        sp = None  # type: ignore
        _sympy_available = False

def is_sympy_available() -> bool:
    """Check if SymPy is available."""
    return _sympy_available


class RationalSimplifier:
    """분수 정규화 (P0-1.1)"""
    
    @staticmethod
    def simplify_fraction(numerator: int, denominator: int) -> Tuple[int, int]:
        """
        gcd를 이용한 분수 정규화
        
        Args:
            numerator: 분자
            denominator: 분모
        
        Returns:
            (정규화된 분자, 정규화된 분모)
        """
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        
        # gcd 계산
        g = gcd(abs(numerator), abs(denominator))
        
        # 분모가 항상 양수가 되도록
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        
        return numerator // g, denominator // g
    
    @staticmethod
    def parse_and_simplify_fraction(num_str: str, den_str: str) -> Optional[Tuple[int, int]]:
        """
        문자열 형식 분수를 파싱하고 정규화
        
        Args:
            num_str: 분자 문자열
            den_str: 분모 문자열
        
        Returns:
            (정규화된 분자, 정규화된 분모) 또는 None
        """
        try:
            num = int(num_str.strip())
            den = int(den_str.strip())
            return RationalSimplifier.simplify_fraction(num, den)
        except (ValueError, ZeroDivisionError):
            return None


class SymbolicEqualityChecker:
    """Symbolic Equality 강화 (P0-1.2)"""
    
    @staticmethod
    def compare_with_all_methods(expr_a: Any, expr_b: Any) -> bool:
        """
        여러 방법을 순차 적용하여 동등성 확인
        
        Args:
            expr_a: 첫 번째 표현식
            expr_b: 두 번째 표현식
        
        Returns:
            동등 여부
        """
        if not is_sympy_available():
            # SymPy 없으면 기본 비교
            return str(expr_a) == str(expr_b)
        
        try:
            sym_a = sp.sympify(expr_a) if not isinstance(expr_a, sp.Basic) else expr_a  # type: ignore[misc]
            sym_b = sp.sympify(expr_b) if not isinstance(expr_b, sp.Basic) else expr_b  # type: ignore[misc]
            
            # 순차적으로 시도
            methods: List[Tuple[str, Callable[[], bool]]] = [  # type: ignore[type-arg]
                ("direct", lambda: sym_a == sym_b),
                ("simplify", lambda: sp.simplify(sym_a - sym_b) == 0),  # type: ignore[operator,misc]
                ("expand", lambda: sp.expand(sym_a - sym_b) == 0),  # type: ignore[operator,misc]
                ("factor", lambda: sp.factor(sym_a - sym_b) == 0),  # type: ignore[operator]
                ("trigsimp", lambda: sp.trigsimp(sym_a - sym_b) == 0),  # type: ignore[operator,misc]
                ("ratsimp", lambda: sp.ratsimp(sym_a - sym_b) == 0),  # type: ignore[operator,misc]
                ("cancel", lambda: sp.cancel(sym_a - sym_b) == 0),  # type: ignore[operator]
                ("nsimplify", lambda: sp.nsimplify(sym_a - sym_b) == 0),  # type: ignore[operator,misc]
            ]
            
            for method_name, method_func in methods:
                try:
                    result = method_func()
                    if result:
                        logger.debug(f"Expressions equal via {method_name}")
                        return True
                except Exception as e:
                    logger.debug(f"Method {method_name} failed: {e}")
                    continue
            
            return False
        except Exception as e:
            logger.debug(f"Symbolic equality check failed: {e}")
            return False
    
    @staticmethod
    def extract_numeric_form(expr: Any) -> Optional[float]:
        """
        표현식을 수치로 변환
        
        Args:
            expr: 표현식
        
        Returns:
            수치 값 또는 None
        """
        if isinstance(expr, (int, float)):
            return float(expr)
        
        if not is_sympy_available():
            return None
        
        try:
            sym_expr = sp.sympify(expr) if not isinstance(expr, sp.Basic) else expr  # type: ignore[misc]
            
            # 자유 기호가 없는 경우만
            if not sym_expr.free_symbols:  # type: ignore[union-attr]
                val = float(sym_expr.evalf())  # type: ignore[union-attr]
                return val
        except Exception:
            pass
        
        return None


class ReverseVerifier:
    """Context 역검증 개선 (P0-1.5)"""
    
    @staticmethod
    def verify_equation_solution(
        solution: Any,
        equation_template: str,
        expected_result: Any,
        tolerance: float = 1e-6
    ) -> bool:
        """
        해가 원래 방정식에서 기대값을 만족하는지 검증
        
        Args:
            solution: 제시된 해
            equation_template: 방정식 템플릿 (예: "{x}^2 - 4 = 0")
            expected_result: 기대값 (예: 0)
            tolerance: 수치 허용 오차
        
        Returns:
            검증 통과 여부
        """
        if not is_sympy_available():
            return True  # SymPy 없으면 검증 스킵
        
        try:
            # 템플릿에 해를 대입
            eq_str = equation_template.replace("{x}", f"({solution})")
            eq = sp.sympify(eq_str)  # type: ignore[misc]
            expected = sp.sympify(str(expected_result))  # type: ignore[misc]
            
            # 수치 계산
            result = eq.evalf()  # type: ignore[union-attr]
            expected_val = expected.evalf()  # type: ignore[union-attr]
            
            # 비교
            diff = abs(float(result) - float(expected_val))  # type: ignore[arg-type]
            return diff < tolerance
        except Exception as e:
            logger.debug(f"Equation verification failed: {e}")
            return False
    
    @staticmethod
    def verify_convergence(
        sequence_values: List[Any],
        limit: Any,
        tolerance: float = 1e-6
    ) -> bool:
        """
        수열이 특정 극한으로 수렴하는지 검증
        
        Args:
            sequence_values: 수열의 값들
            limit: 극한값
            tolerance: 수렴 허용 오차
        
        Returns:
            수렴 여부
        """
        if not sequence_values:
            return False
        
        try:
            limit_val = float(limit)
            # 마지막 값이 극한에 충분히 가까운지 확인
            last_val = float(sequence_values[-1])
            return abs(last_val - limit_val) < tolerance
        except (ValueError, TypeError):
            return False


class ConstraintValidator:
    """제약 조건 검사 (P0-1.6)"""
    
    @staticmethod
    def check_integer(value: Any) -> bool:
        """
        값이 정수인지 확인
        
        Args:
            value: 검사할 값
        
        Returns:
            정수 여부
        """
        try:
            if isinstance(value, int):
                return True
            if isinstance(value, float):
                return value.is_integer()
            # SymPy
            if is_sympy_available() and isinstance(value, sp.Integer):
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def check_positive(value: Any) -> bool:
        """
        값이 양수인지 확인
        
        Args:
            value: 검사할 값
        
        Returns:
            양수 여부
        """
        try:
            num_val = float(value)
            return num_val > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def check_non_negative(value: Any) -> bool:
        """
        값이 음이 아닌 수인지 확인
        
        Args:
            value: 검사할 값
        
        Returns:
            음이 아닌 수 여부
        """
        try:
            num_val = float(value)
            return num_val >= 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def check_modulo(value: Any, modulo: int, remainder: int) -> bool:
        """
        value ≡ remainder (mod modulo) 인지 확인
        
        Args:
            value: 검사할 값
            modulo: 법
            remainder: 나머지
        
        Returns:
            조건 만족 여부
        """
        try:
            int_val = int(value)
            return int_val % modulo == remainder
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def check_range(value: Any, min_val: Any = None, max_val: Any = None) -> bool:
        """
        값이 범위 내에 있는지 확인
        
        Args:
            value: 검사할 값
            min_val: 최솟값 (None이면 체크 안 함)
            max_val: 최댓값 (None이면 체크 안 함)
        
        Returns:
            범위 내 여부
        """
        try:
            num_val = float(value)
            if min_val is not None and num_val < float(min_val):
                return False
            if max_val is not None and num_val > float(max_val):
                return False
            return True
        except (ValueError, TypeError):
            return False


class AdvancedVerificationHelper:
    """P0-1 전체 검증 헬퍼"""
    
    def __init__(self):
        self.rational_simplifier = RationalSimplifier()
        self.symbolic_checker = SymbolicEqualityChecker()
        self.reverse_verifier = ReverseVerifier()
        self.constraint_validator = ConstraintValidator()
    
    def comprehensive_verify(
        self,
        answer: Any,
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        종합적 검증 수행
        
        Args:
            answer: 검증할 답
            context: 검증 컨텍스트
                - expected: 기대값
                - constraints: 제약 조건 리스트
                - equation_template: 방정식 템플릿
                - expected_result: 기대 결과
        
        Returns:
            (검증 통과 여부, 상세 메시지)
        """
        # 1. 제약 조건 검사
        constraints = context.get("constraints", [])
        for constraint in constraints:
            constraint_type = constraint.get("type")
            if constraint_type == "integer":
                if not self.constraint_validator.check_integer(answer):
                    return False, f"Must be integer, got {answer}"
            elif constraint_type == "positive":
                if not self.constraint_validator.check_positive(answer):
                    return False, f"Must be positive, got {answer}"
            elif constraint_type == "non_negative":
                if not self.constraint_validator.check_non_negative(answer):
                    return False, f"Must be non-negative, got {answer}"
            elif constraint_type == "modulo":
                modulo = constraint.get("modulo")
                remainder = constraint.get("remainder", 0)
                if not self.constraint_validator.check_modulo(answer, modulo, remainder):
                    return False, f"Modulo {modulo} constraint failed: got {answer % modulo}, expected {remainder}"
            elif constraint_type == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                if not self.constraint_validator.check_range(answer, min_val, max_val):
                    return False, f"Out of range [{min_val}, {max_val}]: {answer}"
        
        # 2. 기대값과 비교
        expected = context.get("expected")
        if expected is not None:
            # Symbolic 비교
            if not self.symbolic_checker.compare_with_all_methods(answer, expected):
                return False, f"Expected {expected}, got {answer}"
        
        # 3. 역검증 (방정식)
        eq_template = context.get("equation_template")
        if eq_template:
            expected_result = context.get("expected_result", 0)
            if not self.reverse_verifier.verify_equation_solution(
                answer, eq_template, expected_result
            ):
                return False, f"Equation verification failed"
        
        return True, "All checks passed"


# 전역 헬퍼 인스턴스
_GLOBAL_VERIFICATION_HELPER = AdvancedVerificationHelper()


def get_verification_helper() -> AdvancedVerificationHelper:
    """전역 검증 헬퍼 반환"""
    global _GLOBAL_VERIFICATION_HELPER
    return _GLOBAL_VERIFICATION_HELPER
