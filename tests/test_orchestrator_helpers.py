"""
Orchestrator Helper Functions 테스트
"""

import pytest
from src.pipeline.orchestrator_helpers import (
    classify_problem,
    inject_reverse_check,
    attempt_code_fix,
    map_reconciliation_status_to_refine_error,
    classify_mismatch
)


class TestClassifyProblem:
    """문제 분류 테스트"""
    
    def test_geometric_problem(self):
        """기하학 문제 분류 테스트"""
        problem = "Find the area of a triangle with sides 3, 4, 5"
        result = classify_problem(problem)
        assert result == 'geometric'
    
    def test_complex_problem(self):
        """복잡한 문제 분류 테스트"""
        problem = "Prove that for all positive integers n, n^2 is even"
        result = classify_problem(problem)
        assert result == 'complex'
    
    def test_computational_problem(self):
        """계산 문제 분류 테스트"""
        problem = "What is 15 + 27?"
        result = classify_problem(problem)
        assert result == 'computational'
    
    def test_empty_problem(self):
        """빈 문제 테스트"""
        problem = ""
        result = classify_problem(problem)
        assert result == 'computational'  # 기본값


class TestInjectReverseCheck:
    """역검증 훅 주입 테스트"""
    
    def test_simple_addition(self):
        """간단한 덧셈 문제 테스트"""
        problem = "What is 15 + 27?"
        variables = {}
        inject_reverse_check(problem, variables)
        
        assert 'reverse_func' in variables
        assert variables['reverse_func'](42) == True
        assert variables['reverse_func'](43) == False
    
    def test_simple_subtraction(self):
        """간단한 뺄셈 문제 테스트"""
        problem = "Compute 100 - 25"
        variables = {}
        inject_reverse_check(problem, variables)
        
        assert 'reverse_func' in variables
        assert variables['reverse_func'](75) == True
    
    def test_no_match(self):
        """매칭되지 않는 문제 테스트"""
        problem = "Solve the equation x^2 + 5x + 6 = 0"
        variables = {}
        inject_reverse_check(problem, variables)
        
        assert 'reverse_func' not in variables


class TestAttemptCodeFix:
    """코드 수정 시도 테스트"""
    
    def test_timeout_error(self):
        """타임아웃 에러 테스트"""
        code = "while True: pass"
        error = "Timeout: Code execution exceeded time limit"
        result = attempt_code_fix(code, error)
        # 현재는 None을 반환 (실제로는 LLM을 통해 수정)
        assert result is None
    
    def test_syntax_error(self):
        """문법 에러 테스트"""
        code = "print('hello"
        error = "SyntaxError: EOL while scanning string literal"
        result = attempt_code_fix(code, error)
        # 현재는 None을 반환 (실제로는 LLM을 통해 수정)
        assert result is None
    
    def test_unknown_error(self):
        """알 수 없는 에러 테스트"""
        code = "x = 1 / 0"
        error = "ZeroDivisionError: division by zero"
        result = attempt_code_fix(code, error)
        assert result is None


class TestMapReconciliationStatus:
    """Reconciliation 상태 매핑 테스트"""
    
    def test_arithmetic_mismatch(self):
        """산술 불일치 테스트"""
        result = map_reconciliation_status_to_refine_error('MISMATCH_ARITHMETIC')
        assert result == 'arithmetic'
    
    def test_logic_mismatch(self):
        """논리 불일치 테스트"""
        result = map_reconciliation_status_to_refine_error('MISMATCH_LOGIC')
        assert result == 'logic'
    
    def test_parsing_error(self):
        """파싱 에러 테스트"""
        result = map_reconciliation_status_to_refine_error('ERROR_PARSING')
        assert result == 'other'
    
    def test_format_diff(self):
        """형식 차이 테스트"""
        result = map_reconciliation_status_to_refine_error('MISMATCH_FORMAT_DIFF')
        assert result == 'format'
    
    def test_unknown_status(self):
        """알 수 없는 상태 테스트"""
        result = map_reconciliation_status_to_refine_error('UNKNOWN_STATUS')
        assert result == 'other'


class TestClassifyMismatch:
    """불일치 분류 테스트"""
    
    def test_numeric_format_diff(self):
        """숫자 형식 차이 테스트"""
        result = classify_mismatch("42", "42.0")
        assert result == 'format'
    
    def test_numeric_arithmetic_diff(self):
        """숫자 산술 차이 테스트"""
        result = classify_mismatch("42", "43")
        assert result == 'arithmetic'
    
    def test_symbolic_format_diff(self):
        """심볼릭 형식 차이 테스트"""
        result = classify_mismatch("x^2", "x**2")
        # sympy가 설치되어 있으면 'format', 없으면 'other'
        assert result in ['format', 'other']
    
    def test_symbolic_logic_diff(self):
        """심볼릭 논리 차이 테스트"""
        result = classify_mismatch("x^2", "x^3")
        # sympy가 설치되어 있으면 'logic', 없으면 'other'
        assert result in ['logic', 'other']
    
    def test_invalid_input(self):
        """잘못된 입력 테스트"""
        result = classify_mismatch("invalid", "also invalid")
        assert result == 'other'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
