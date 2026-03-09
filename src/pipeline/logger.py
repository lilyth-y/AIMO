"""
로깅 유틸리티 모듈
구조화된 로깅을 제공합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로 (None이면 콘솔만)
        level: 로그 레벨
        format_string: 커스텀 포맷 문자열
    
    Returns:
        설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        return logger
    
    # 포맷 설정
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택적)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 전역 로거 인스턴스
_pipeline_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    전역 파이프라인 로거를 반환합니다.
    
    Returns:
        파이프라인 로거
    """
    global _pipeline_logger
    
    if _pipeline_logger is None:
        from .settings import settings
        log_file = settings.log_path.parent / "pipeline.log"
        _pipeline_logger = setup_logger(
            "pipeline",
            log_file=log_file,
            level=logging.INFO
        )
    
    return _pipeline_logger
