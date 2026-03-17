"""
통합 설정 관리 모듈
- 환경 변수 기반 설정
- 설정 검증
- 타입 안전성 보장
"""

import os
from typing import Optional
from pathlib import Path


class Settings:
    """통합 설정 클래스"""
    
    # 모델 설정
    @property
    def model_name(self) -> str:
        """사용할 모델 이름 (HuggingFace repo_id 또는 로컬 절대경로).
        기본값: 1.5B (빠른 평가). Kaggle/긴 세션에서는 OMI_MODEL=MathLLMs/MathCoder-L-13B 로 13B 사용 가능."""
        return os.getenv(
            "OMI_MODEL",
            os.getenv("AIMO_MODEL", "Qwen/Qwen2.5-Math-1.5B-Instruct")
        )
    
    @property
    def quantization(self) -> str:
        """양자화 설정"""
        return os.getenv(
            "OMI_QUANTIZATION",
            os.getenv(
                "AIMO_QUANTIZATION",
                "8bit"
            )
        )
    
    # 파이프라인 설정
    @property
    def use_structured(self) -> bool:
        """Structured reasoning 사용 여부"""
        return os.getenv("OMI_USE_STRUCTURED", "true").lower() == "true"
    
    @property
    def structured_length_threshold(self) -> int:
        """Structured reasoning 길이 임계값"""
        return int(os.getenv("OMI_STRUCTURED_LENGTH_THRESHOLD", "120"))
    
    @property
    def complexity_structured_min_score(self) -> int:
        """Structured reasoning 최소 복잡도 점수"""
        return int(os.getenv("OMI_COMPLEXITY_STRUCTURED_MIN_SCORE", "5"))
    
    @property
    def decomposition_complexity_threshold(self) -> int:
        """문제 분해 복잡도 임계값"""
        return int(os.getenv("OMI_DECOMPOSITION_COMPLEXITY_THRESHOLD", "15"))
    
    # 후보 생성 설정
    @property
    def num_candidates(self) -> int:
        """전략당 생성할 후보 수"""
        return int(os.getenv("OMI_NUM_CANDIDATES", "3"))
    
    @property
    def use_voting(self) -> bool:
        """후보 투표 사용 여부"""
        return os.getenv("OMI_USE_VOTING", "false").lower() == "true"
    
    # 로깅 설정
    @property
    def log_path(self) -> Path:
        """로그 파일 경로"""
        log_path_str = os.getenv("OMI_LOG_PATH", "logs/eval_log.jsonl")
        return Path(log_path_str)
    
    # HuggingFace 설정
    @property
    def hf_home(self) -> Optional[Path]:
        """HuggingFace 홈 디렉토리"""
        hf_home_str = os.getenv("HF_HOME")
        if hf_home_str:
            return Path(hf_home_str)
        return None
    
    @property
    def transformers_cache(self) -> Optional[Path]:
        """Transformers 캐시 디렉토리"""
        cache_str = os.getenv("TRANSFORMERS_CACHE")
        if cache_str:
            return Path(cache_str)
        return None
    
    # 실행 설정
    @property
    def executor_timeout_seconds(self) -> float:
        """코드 실행 타임아웃 (초)"""
        return float(os.getenv("OMI_EXECUTOR_TIMEOUT", "5.0"))
    
    @property
    def executor_memory_limit_mb(self) -> int:
        """코드 실행 메모리 제한 (MB). 0이면 제한 없음."""
        return int(os.getenv("AIMO_EXECUTOR_MEMORY_MB", "0"))
    
    # 테스트 설정
    @property
    def fast_test(self) -> bool:
        """빠른 테스트 모드"""
        return os.getenv("AIMO_FAST_TEST", "0") == "1"
    
    @property
    def refine_max_iterations(self) -> int:
        """Refine 루프 최대 반복 횟수"""
        return int(os.getenv("OMI_REFINE_MAX_ITERATIONS", "3"))
    
    @property
    def refine_enabled(self) -> bool:
        """Refine 루프 활성화 여부"""
        return os.getenv("OMI_REFINE_ENABLED", "true").lower() == "true"
    
    def validate(self) -> list[str]:
        """
        설정을 검증하고 문제가 있으면 경고 리스트를 반환합니다.
        
        Returns:
            경고 메시지 리스트
        """
        warnings = []
        
        # 모델 경로 검증
        if not os.path.exists(self.model_name) and not self.model_name.startswith(("http://", "https://")):
            # HuggingFace 모델 이름이거나 로컬 경로일 수 있음
            if not any(char in self.model_name for char in ["/", "\\"]):
                # HuggingFace 모델 이름인 경우 경고 없음
                pass
            elif not Path(self.model_name).exists():
                warnings.append(f"모델 경로가 존재하지 않습니다: {self.model_name}")
        
        # 양자화 설정 검증
        if self.quantization not in ["4bit", "8bit", "none", ""]:
            warnings.append(f"알 수 없는 양자화 설정: {self.quantization}")
        
        # 로그 디렉토리 생성
        log_dir = self.log_path.parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
            warnings.append(f"로그 디렉토리를 생성했습니다: {log_dir}")
        
        return warnings
    
    def __repr__(self) -> str:
        """설정 요약 문자열"""
        return f"""Settings(
    model={self.model_name[:50]}...,
    quantization={self.quantization},
    use_structured={self.use_structured},
    log_path={self.log_path}
)"""


# 전역 설정 인스턴스
settings = Settings()
