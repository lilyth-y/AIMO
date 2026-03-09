"""
Config 모듈 하위 호환성 테스트
새로운 settings.py와 기존 config.py의 호환성 확인
"""

import pytest
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import config
from src.pipeline.settings import settings


class TestConfigCompatibility:
    """Config 하위 호환성 테스트"""
    
    def test_use_structured_exists(self):
        """USE_STRUCTURED 존재 확인"""
        assert hasattr(config, 'USE_STRUCTURED')
        assert isinstance(config.USE_STRUCTURED, bool)
    
    def test_structured_length_threshold_exists(self):
        """STRUCTURED_LENGTH_THRESHOLD 존재 확인"""
        assert hasattr(config, 'STRUCTURED_LENGTH_THRESHOLD')
        assert isinstance(config.STRUCTURED_LENGTH_THRESHOLD, int)
    
    def test_complexity_structured_min_score_exists(self):
        """COMPLEXITY_STRUCTURED_MIN_SCORE 존재 확인"""
        assert hasattr(config, 'COMPLEXITY_STRUCTURED_MIN_SCORE')
        assert isinstance(config.COMPLEXITY_STRUCTURED_MIN_SCORE, int)
    
    def test_log_path_exists(self):
        """LOG_PATH 존재 확인"""
        assert hasattr(config, 'LOG_PATH')
        assert isinstance(config.LOG_PATH, str)
    
    def test_num_candidates_exists(self):
        """NUM_CANDIDATES 존재 확인"""
        assert hasattr(config, 'NUM_CANDIDATES')
        assert isinstance(config.NUM_CANDIDATES, int)
    
    def test_use_voting_exists(self):
        """USE_VOTING 존재 확인"""
        assert hasattr(config, 'USE_VOTING')
        assert isinstance(config.USE_VOTING, bool)
    
    def test_hf_model_name_exists(self):
        """HF_MODEL_NAME 존재 확인"""
        assert hasattr(config, 'HF_MODEL_NAME')
        assert isinstance(config.HF_MODEL_NAME, str)
    
    def test_quantization_default_exists(self):
        """QUANTIZATION_DEFAULT 존재 확인"""
        assert hasattr(config, 'QUANTIZATION_DEFAULT')
        assert isinstance(config.QUANTIZATION_DEFAULT, str)
    
    def test_decomposition_complexity_threshold_exists(self):
        """DECOMPOSITION_COMPLEXITY_THRESHOLD 존재 확인"""
        assert hasattr(config, 'DECOMPOSITION_COMPLEXITY_THRESHOLD')
        assert isinstance(config.DECOMPOSITION_COMPLEXITY_THRESHOLD, int)
    
    def test_config_matches_settings(self):
        """Config 값이 Settings와 일치하는지 확인"""
        # settings.py가 import 가능한 경우에만 테스트
        try:
            assert config.USE_STRUCTURED == settings.use_structured
            assert config.STRUCTURED_LENGTH_THRESHOLD == settings.structured_length_threshold
            assert config.COMPLEXITY_STRUCTURED_MIN_SCORE == settings.complexity_structured_min_score
            assert config.LOG_PATH == str(settings.log_path)
            assert config.NUM_CANDIDATES == settings.num_candidates
            assert config.USE_VOTING == settings.use_voting
            assert config.HF_MODEL_NAME == settings.model_name
            assert config.QUANTIZATION_DEFAULT == settings.quantization
            assert config.DECOMPOSITION_COMPLEXITY_THRESHOLD == settings.decomposition_complexity_threshold
        except ImportError:
            # settings.py가 없으면 스킵
            pytest.skip("settings.py not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
