"""
프로젝트 전용 예외 클래스
명확한 에러 타입을 정의합니다.
"""


class PipelineError(Exception):
    """파이프라인 기본 예외"""
    pass


class CodeGenerationError(PipelineError):
    """코드 생성 실패"""
    pass


class CodeExecutionError(PipelineError):
    """코드 실행 실패"""
    
    def __init__(self, message: str, code: str = "", error_type: str = "unknown"):
        super().__init__(message)
        self.code = code
        self.error_type = error_type


class VerificationError(PipelineError):
    """검증 실패"""
    
    def __init__(self, message: str, answer: str = "", expected: str = ""):
        super().__init__(message)
        self.answer = answer
        self.expected = expected


class TimeoutError(PipelineError):
    """타임아웃 에러"""
    
    def __init__(self, message: str, timeout_seconds: float = 0.0):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class ModelLoadError(PipelineError):
    """모델 로드 실패"""
    pass


class ConfigurationError(PipelineError):
    """설정 오류"""
    pass
