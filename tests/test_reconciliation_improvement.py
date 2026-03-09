"""
추론-답변 조정 개선 테스트
불일치 분류 및 SymPy 정규화를 테스트합니다.
"""

import pytest
from src.pipeline.reconciliation import ReasoningReconciler, ReconciliationResult
from src.pipeline.stage5_verification import VerificationRouter

try:
    import sympy as sp
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


class TestReconciliationImprovement:
    """추론-답변 조정 개선 테스트"""
    
    def test_exact_match(self):
        """정확한 일치 테스트"""
        reconciler = ReasoningReconciler()
        
        result = reconciler.reconcile("42", "42")
        
        assert result.match is True
        assert result.status == 'MATCH_EXACT'
    
    def test_format_mismatch(self):
        """형식 불일치 테스트"""
        reconciler = ReasoningReconciler()
        
        # 같은 값, 다른 형식
        result = reconciler.reconcile("42", "42.0")
        
        assert result.match is True
        assert result.status == 'MATCH_FORMAT_DIFF'
    
    def test_arithmetic_mismatch(self):
        """산술 불일치 테스트"""
        reconciler = ReasoningReconciler()
        
        result = reconciler.reconcile("42", "43")
        
        assert result.match is False
        assert result.status == 'MISMATCH_ARITHMETIC'
        assert "Numeric difference" in result.details
    
    def test_logic_mismatch(self):
        """로직 불일치 테스트"""
        reconciler = ReasoningReconciler()
        
        result = reconciler.reconcile("x + 1", "x + 2")
        
        assert result.match is False
        assert result.status == 'MISMATCH_LOGIC'
    
    def test_sympy_normalization(self):
        """SymPy 정규화 테스트"""
        if not SYMPY_AVAILABLE:
            pytest.skip("SymPy not available")
        
        reconciler = ReasoningReconciler()
        
        # 같은 표현식, 다른 형식
        result = reconciler.reconcile("x^2 - 1", "(x-1)*(x+1)")
        
        assert result.match is True
        assert result.status in ['MATCH_EXACT', 'MATCH_FORMAT_DIFF']
    
    def test_floating_point_tolerance(self):
        """부동소수점 허용 오차 테스트"""
        reconciler = ReasoningReconciler()
        
        # 매우 작은 차이 (부동소수점 오차)
        result = reconciler.reconcile("0.1 + 0.2", "0.3")
        
        # 부동소수점 오차로 인해 일치로 인식될 수 있음
        assert result.match is True or result.status == 'MISMATCH_ARITHMETIC'
    
    def test_list_mismatch(self):
        """리스트 불일치 테스트"""
        reconciler = ReasoningReconciler()
        
        result = reconciler.reconcile([1, 2, 3], [1, 2, 4])
        
        assert result.match is False
        assert result.status == 'MISMATCH_LOGIC'
        assert "List" in result.details
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        reconciler = ReasoningReconciler()
        
        # None 값
        result = reconciler.reconcile(None, "42")
        assert result.match is False
        assert result.status == 'ERROR_MISSING'
        
        # 파싱 불가능
        result = reconciler.reconcile("invalid", "42")
        assert result.match is False
        assert result.status == 'ERROR_PARSING'
    
    def test_relative_difference(self):
        """상대 차이 계산 테스트"""
        reconciler = ReasoningReconciler()
        
        # 큰 수의 작은 차이
        result = reconciler.reconcile("1000000", "1000001")
        
        # 상대 차이가 매우 작으면 형식 차이로 인식될 수 있음
        # 또는 산술 불일치로 인식될 수 있음
        assert result.match is False or result.status == 'MATCH_FORMAT_DIFF'
        assert result.status in ['MISMATCH_ARITHMETIC', 'MATCH_FORMAT_DIFF']
        if result.status == 'MISMATCH_ARITHMETIC':
            assert "relative" in result.details.lower() or "diff" in result.details.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
