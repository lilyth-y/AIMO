"""
Settings 모듈 테스트
"""

import pytest
import os
from pathlib import Path
from src.pipeline.settings import Settings, settings


class TestSettings:
    """Settings 클래스 테스트"""
    
    def test_default_model_name(self):
        """기본 모델 이름 테스트"""
        # 환경 변수 제거
        old_value = os.environ.get("OMI_MODEL")
        if "OMI_MODEL" in os.environ:
            del os.environ["OMI_MODEL"]
        if "AIMO_MODEL" in os.environ:
            del os.environ["AIMO_MODEL"]
        
        s = Settings()
        model = s.model_name
        assert model is not None
        assert isinstance(model, str)
        
        # 복원
        if old_value:
            os.environ["OMI_MODEL"] = old_value
    
    def test_environment_override(self):
        """환경 변수 오버라이드 테스트"""
        os.environ["OMI_MODEL"] = "test-model"
        s = Settings()
        assert s.model_name == "test-model"
        del os.environ["OMI_MODEL"]
    
    def test_quantization(self):
        """양자화 설정 테스트"""
        s = Settings()
        quant = s.quantization
        assert quant in ["4bit", "8bit", "none", ""]
    
    def test_use_structured(self):
        """Structured reasoning 설정 테스트"""
        s = Settings()
        assert isinstance(s.use_structured, bool)
    
    def test_structured_length_threshold(self):
        """Structured length threshold 테스트"""
        s = Settings()
        assert isinstance(s.structured_length_threshold, int)
        assert s.structured_length_threshold > 0
    
    def test_complexity_structured_min_score(self):
        """Complexity structured min score 테스트"""
        s = Settings()
        assert isinstance(s.complexity_structured_min_score, int)
        assert s.complexity_structured_min_score >= 0
    
    def test_decomposition_complexity_threshold(self):
        """Decomposition complexity threshold 테스트"""
        s = Settings()
        assert isinstance(s.decomposition_complexity_threshold, int)
        assert s.decomposition_complexity_threshold > 0
    
    def test_num_candidates(self):
        """Num candidates 테스트"""
        s = Settings()
        assert isinstance(s.num_candidates, int)
        assert s.num_candidates > 0
    
    def test_use_voting(self):
        """Use voting 테스트"""
        s = Settings()
        assert isinstance(s.use_voting, bool)
    
    def test_log_path(self):
        """Log path 테스트"""
        s = Settings()
        assert isinstance(s.log_path, Path)
    
    def test_executor_timeout(self):
        """Executor timeout 테스트"""
        s = Settings()
        assert isinstance(s.executor_timeout_seconds, float)
        assert s.executor_timeout_seconds > 0
    
    def test_executor_memory_limit(self):
        """Executor memory limit 테스트"""
        s = Settings()
        assert isinstance(s.executor_memory_limit_mb, int)
        assert s.executor_memory_limit_mb > 0
    
    def test_fast_test(self):
        """Fast test 설정 테스트"""
        s = Settings()
        assert isinstance(s.fast_test, bool)


class TestSettingsValidation:
    """Settings 검증 테스트"""
    
    def test_validate_default(self):
        """기본 설정 검증 테스트"""
        s = Settings()
        warnings = s.validate()
        # 경고가 있어도 정상 (모델 경로가 없을 수 있음)
        assert isinstance(warnings, list)
    
    def test_validate_invalid_quantization(self):
        """잘못된 양자화 설정 검증 테스트"""
        os.environ["OMI_QUANTIZATION"] = "invalid"
        s = Settings()
        warnings = s.validate()
        # 경고가 있어야 함
        assert any("양자화" in w or "quantization" in w.lower() for w in warnings)
        del os.environ["OMI_QUANTIZATION"]
    
    def test_log_directory_creation(self):
        """로그 디렉토리 생성 테스트"""
        s = Settings()
        log_dir = s.log_path.parent
        # validate()가 디렉토리를 생성해야 함
        warnings = s.validate()
        assert log_dir.exists() or any("생성" in w for w in warnings)


class TestGlobalSettings:
    """전역 settings 인스턴스 테스트"""
    
    def test_global_instance(self):
        """전역 인스턴스 테스트"""
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_global_instance_access(self):
        """전역 인스턴스 접근 테스트"""
        model = settings.model_name
        assert model is not None
    
    def test_repr(self):
        """__repr__ 테스트"""
        repr_str = repr(settings)
        assert isinstance(repr_str, str)
        assert "Settings" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
