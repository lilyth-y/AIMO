"""
고급 검증 모듈 테스트
SymPy 기반 고급 검증 기능을 테스트합니다.
"""

import pytest
from src.pipeline.stage5_verification import VerificationRouter

try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


class TestAdvancedVerification:
    """고급 검증 기능 테스트"""
    
    def test_rational_simplification(self):
        """유리수 단순화 검증 테스트"""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy not available")
        
        verifier = VerificationRouter()
        
        # 1/2와 0.5 비교
        assert verifier._compare(0.5, sp.Rational(1, 2))
        
        # 2/3과 0.666... 비교
        assert verifier._compare(2/3, sp.Rational(2, 3))
        
        # 1/3 * 3 = 1
        assert verifier._compare(sp.Rational(1, 3) * 3, 1)
    
    def test_symbolic_equality(self):
        """기호 등식 검증 테스트"""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy not available")
        
        verifier = VerificationRouter()
        
        # x^2 - 1 = (x-1)(x+1)
        x = sp.Symbol('x')
        expr1 = x**2 - 1
        expr2 = (x - 1) * (x + 1)
        assert verifier._compare(expr1, expr2)
        
        # sin^2(x) + cos^2(x) = 1
        assert verifier._compare(sp.sin(x)**2 + sp.cos(x)**2, 1)
        
        # (x+1)^2 = x^2 + 2*x + 1
        assert verifier._compare((x + 1)**2, x**2 + 2*x + 1)
    
    def test_numeric_tolerance(self):
        """부동소수점 수치 허용 오차 테스트"""
        verifier = VerificationRouter(rel_tol=1e-6, abs_tol=1e-8)
        
        # 근사값 비교
        assert verifier._compare(3.1415926535, 3.1415926536)
        assert verifier._compare(0.1 + 0.2, 0.3)  # 부동소수점 오차
        
        # 큰 수 비교
        assert verifier._compare(1e10, 1e10 + 1e-5)
        
        # 작은 수 비교
        assert verifier._compare(1e-10, 1e-10 + 1e-18)
    
    def test_list_multiset_comparison(self):
        """리스트 다중집합 비교 테스트"""
        verifier = VerificationRouter()
        
        # 순서가 다른 숫자 리스트
        assert verifier._compare([1, 2, 3], [3, 1, 2])
        assert verifier._compare([1.0, 2.0, 3.0], [3, 2, 1])
        
        # 중복 요소 포함
        assert verifier._compare([1, 2, 2, 3], [2, 1, 3, 2])
        
        # 다른 길이
        assert not verifier._compare([1, 2, 3], [1, 2])
    
    def test_set_multiset_comparison(self):
        """집합 다중집합 비교 테스트"""
        verifier = VerificationRouter()
        
        # 같은 요소, 다른 순서
        assert verifier._compare({1, 2, 3}, {3, 1, 2})
        
        # 다른 요소
        assert not verifier._compare({1, 2, 3}, {1, 2, 4})
        
        # 다른 길이
        assert not verifier._compare({1, 2, 3}, {1, 2})
    
    def test_expression_normalization(self):
        """표현식 정규화 테스트"""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy not available")
        
        verifier = VerificationRouter()
        
        x = sp.Symbol('x')
        
        # factor vs expand
        assert verifier._compare(sp.factor(x**2 - 1), sp.expand((x-1)*(x+1)))
        
        # simplify
        assert verifier._compare(sp.simplify(x**2 + 2*x + 1), (x + 1)**2)
        
        # trigsimp
        assert verifier._compare(sp.sin(x)**2 + sp.cos(x)**2, 1)
    
    def test_reverse_check(self):
        """역검증 테스트"""
        verifier = VerificationRouter()
        
        # Callable reverse function
        def rev_func(ans):
            return ans == 42
        
        context = {'reverse_func': rev_func}
        assert verifier._reverse_check(42, context)
        assert not verifier._reverse_check(43, context)
        
        # Expression template
        if SYMPY_AVAILABLE:
            context = {
                'reverse_expression': '{x} * 2',
                'reverse_target': 10
            }
            assert verifier._reverse_check(5, context)  # 5 * 2 = 10
            assert not verifier._reverse_check(4, context)  # 4 * 2 != 10
    
    def test_constraint_check(self):
        """제약 조건 검사 테스트"""
        verifier = VerificationRouter()
        
        # Integer constraint
        assert verifier._check_constraints(42, ['integer'])
        assert not verifier._check_constraints(42.5, ['integer'])
        
        # Non-negative constraint
        assert verifier._check_constraints(42, ['non_negative'])
        assert not verifier._check_constraints(-1, ['non_negative'])
        
        # Modulo constraint
        assert verifier._check_constraints(5, ['modulo_10'])
        assert not verifier._check_constraints(15, ['modulo_10'])
    
    def test_parse_answer(self):
        """답변 파싱 테스트"""
        verifier = VerificationRouter()
        
        # Integer
        assert verifier._parse_answer("42") == 42
        
        # Float
        assert verifier._parse_answer("3.14") == 3.14
        
        # LaTeX fraction
        if SYMPY_AVAILABLE:
            parsed = verifier._parse_answer("\\frac{1}{2}")
            assert parsed is not None
        
        # List
        assert verifier._parse_answer("[1, 2, 3]") == [1, 2, 3]
        
        # None
        assert verifier._parse_answer(None) is None
        assert verifier._parse_answer("") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
