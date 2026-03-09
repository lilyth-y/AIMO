"""
RefineLoop 모듈 테스트
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.pipeline.refine_loop import RefineLoop, create_refine_loop


class TestRefineLoop:
    """RefineLoop 클래스 테스트"""
    
    def test_init(self):
        """초기화 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        assert loop.max_iterations == 3
        assert loop.enable_loop == True
        assert loop.iteration_count == 0
    
    def test_should_refine_conditions(self):
        """should_refine 조건 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        
        # 검증 통과 시 refine 불필요
        assert loop.should_refine(True, True, False) == False
        
        # Structured reasoning 없으면 refine 불필요
        assert loop.should_refine(False, False, False) == False
        
        # Structured reasoning 있고 검증 실패하면 refine 필요
        assert loop.should_refine(True, False, False) == True
    
    def test_should_refine_max_iterations(self):
        """최대 반복 횟수 테스트"""
        loop = RefineLoop(max_iterations=2, enable_loop=True)
        loop.iteration_count = 2
        
        # 최대 반복 횟수 도달
        assert loop.should_refine(True, False, True) == False
    
    def test_should_refine_disabled(self):
        """루프 비활성화 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=False)
        
        # 루프 비활성화 시 refine 불필요
        assert loop.should_refine(True, False, False) == False
    
    def test_refine_attempt_success(self):
        """Refine 시도 성공 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        
        # Mock 객체 생성
        solver = Mock()
        solver.last_reasoning = "<ANS>42</ANS>"
        solver.generate_code_from_prompt = Mock(return_value="print(42)")
        
        executor = Mock()
        executor.execute = Mock(return_value="42")
        executor.execute_with_stats = Mock(return_value=("42", None))
        
        verifier = Mock()
        verifier.verify = Mock(return_value=True)
        
        reconciler = Mock()
        reconcile_result = Mock()
        reconcile_result.match = True
        reconcile_result.status = 'MATCH_EXACT'
        reconcile_result.details = ""
        reconciler.reconcile = Mock(return_value=reconcile_result)
        
        # Refine 시도
        result, success = loop.refine_attempt(
            solver=solver,
            executor=executor,
            verifier=verifier,
            reconciler=reconciler,
            problem_text="What is 2 + 2?",
            previous_reasoning="<ANS>4</ANS>",
            previous_code="print(2+2)",
            execution_result="4",
            extracted_answer="4",
            mismatch_type=None,
            variables={},
            strategy="Path A: The Simulator"
        )
        
        assert success == True
        assert result is not None
        assert result['verified'] == True
        assert result['refine'] == True
        assert result['refine_iteration'] == 1
        assert loop.iteration_count == 1
    
    def test_refine_attempt_failure(self):
        """Refine 시도 실패 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        
        # Mock 객체 생성
        solver = Mock()
        solver.last_reasoning = "<ANS>42</ANS>"
        solver.generate_code_from_prompt = Mock(return_value="print(42)")
        
        executor = Mock()
        executor.execute = Mock(return_value="43")
        executor.execute_with_stats = Mock(return_value=("43", None))
        
        verifier = Mock()
        verifier.verify = Mock(return_value=False)  # 검증 실패
        
        reconciler = Mock()
        reconcile_result = Mock()
        reconcile_result.match = False
        reconcile_result.status = 'MISMATCH_ARITHMETIC'
        reconcile_result.details = "Numeric difference"
        reconciler.reconcile = Mock(return_value=reconcile_result)
        
        # Refine 시도
        result, success = loop.refine_attempt(
            solver=solver,
            executor=executor,
            verifier=verifier,
            reconciler=reconciler,
            problem_text="What is 2 + 2?",
            previous_reasoning="<ANS>4</ANS>",
            previous_code="print(2+2)",
            execution_result="3",
            extracted_answer="4",
            mismatch_type="MISMATCH_ARITHMETIC",
            variables={},
            strategy="Path A: The Simulator"
        )
        
        assert success == False
        assert result is None
        assert loop.iteration_count == 1
    
    def test_reset(self):
        """리셋 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        loop.iteration_count = 2
        
        loop.reset()
        
        assert loop.iteration_count == 0
    
    def test_can_continue(self):
        """계속 가능 여부 테스트"""
        loop = RefineLoop(max_iterations=3, enable_loop=True)
        
        # 반복 횟수 미만
        assert loop.can_continue() == True
        
        # 반복 횟수 도달
        loop.iteration_count = 3
        assert loop.can_continue() == False


class TestCreateRefineLoop:
    """create_refine_loop 함수 테스트"""
    
    def test_create_default(self):
        """기본 설정으로 생성"""
        loop = create_refine_loop()
        assert isinstance(loop, RefineLoop)
        assert loop.max_iterations == 3
        assert loop.enable_loop == True
    
    def test_create_custom(self):
        """커스텀 설정으로 생성"""
        loop = create_refine_loop(max_iterations=5, enable_loop=False)
        assert loop.max_iterations == 5
        assert loop.enable_loop == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
