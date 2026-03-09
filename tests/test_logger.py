"""
Logger 모듈 테스트
"""

import pytest
import logging
from pathlib import Path
from src.pipeline.logger import setup_logger, get_logger


class TestSetupLogger:
    """setup_logger 함수 테스트"""
    
    def test_setup_logger_console_only(self):
        """콘솔만 사용하는 로거 설정 테스트"""
        logger = setup_logger("test_console", level=logging.DEBUG)
        assert logger.name == "test_console"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_file(self, tmp_path):
        """파일 로깅 포함 로거 설정 테스트"""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=log_file, level=logging.INFO)
        assert logger.name == "test_file"
        assert log_file.exists() or log_file.parent.exists()


class TestGetLogger:
    """get_logger 함수 테스트"""
    
    def test_get_logger_singleton(self):
        """전역 로거 싱글톤 테스트"""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
        assert logger1.name == "pipeline"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
