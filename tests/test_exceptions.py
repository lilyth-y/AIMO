"""
Exceptions 모듈 테스트
"""

import pytest
from src.pipeline.exceptions import (
    PipelineError,
    CodeGenerationError,
    CodeExecutionError,
    VerificationError,
    TimeoutError,
    ModelLoadError,
    ConfigurationError
)


class TestPipelineError:
    """PipelineError 기본 예외 테스트"""
    
    def test_pipeline_error(self):
        """기본 예외 생성 테스트"""
        error = PipelineError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)


class TestCodeGenerationError:
    """CodeGenerationError 테스트"""
    
    def test_code_generation_error(self):
        """코드 생성 에러 테스트"""
        error = CodeGenerationError("Failed to generate code")
        assert str(error) == "Failed to generate code"
        assert isinstance(error, PipelineError)


class TestCodeExecutionError:
    """CodeExecutionError 테스트"""
    
    def test_code_execution_error(self):
        """코드 실행 에러 테스트"""
        error = CodeExecutionError("Execution failed", code="print('test')", error_type="syntax")
        assert str(error) == "Execution failed"
        assert error.code == "print('test')"
        assert error.error_type == "syntax"
        assert isinstance(error, PipelineError)


class TestVerificationError:
    """VerificationError 테스트"""
    
    def test_verification_error(self):
        """검증 에러 테스트"""
        error = VerificationError("Verification failed", answer="42", expected="43")
        assert str(error) == "Verification failed"
        assert error.answer == "42"
        assert error.expected == "43"
        assert isinstance(error, PipelineError)


class TestTimeoutError:
    """TimeoutError 테스트"""
    
    def test_timeout_error(self):
        """타임아웃 에러 테스트"""
        error = TimeoutError("Operation timed out", timeout_seconds=5.0)
        assert str(error) == "Operation timed out"
        assert error.timeout_seconds == 5.0
        assert isinstance(error, PipelineError)


class TestModelLoadError:
    """ModelLoadError 테스트"""
    
    def test_model_load_error(self):
        """모델 로드 에러 테스트"""
        error = ModelLoadError("Failed to load model")
        assert str(error) == "Failed to load model"
        assert isinstance(error, PipelineError)


class TestConfigurationError:
    """ConfigurationError 테스트"""
    
    def test_configuration_error(self):
        """설정 에러 테스트"""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, PipelineError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
