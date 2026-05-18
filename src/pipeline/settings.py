"""
통합 설정 관리 모듈
- 환경 변수 기반 설정
- 설정 검증
- 타입 안전성 보장
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from .executor_env import executor_wall_seconds_from_env

# .env 파일 로드 (최상위 디렉토리 기준)
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class Settings:
    """통합 설정 클래스"""
    
    # 모델 설정
    @property
    def model_name(self) -> str:
        """사용할 모델 이름 (HuggingFace repo_id 또는 로컬 절대경로).
        기본값: Qwen2.5-Math-7B-Instruct. VRAM 부족·스모크용으로 1.5B를 쓰려면
        AIMO_MODEL=Qwen/Qwen2.5-Math-1.5B-Instruct."""
        return os.getenv(
            "OMI_MODEL",
            os.getenv("AIMO_MODEL", "Qwen/Qwen2.5-Math-7B-Instruct")
        )
    
    @property
    def quantization(self) -> str:
        """양자화 설정"""
        return os.getenv(
            "OMI_QUANTIZATION",
            os.getenv(
                "AIMO_QUANTIZATION",
                "4bit",
            ),
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
    
    @property
    def optimize_accuracy(self) -> bool:
        """
        정확도 우선 모드 (Ralph 루프·벤치 평가용).
        ``1``이면 후보 투표 기본 활성, 후보 수 기본 4(환경으로 덮어쓰기 가능).
        """
        return os.getenv("AIMO_OPTIMIZE_ACCURACY", "0").strip() == "1"

    # 후보 생성 설정
    @property
    def num_candidates(self) -> int:
        """전략당 생성할 후보 수 (optimize_accuracy 시 기본 4, 아니면 3)."""
        raw = os.getenv("OMI_NUM_CANDIDATES")
        if raw is None or str(raw).strip() == "":
            return 4 if self.optimize_accuracy else 3
        return max(1, int(raw))
    
    @property
    def use_voting(self) -> bool:
        """후보 투표 사용 여부 (optimize_accuracy 시 기본 true)."""
        if self.optimize_accuracy:
            return os.getenv("OMI_USE_VOTING", "true").lower() == "true"
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
        """코드 실행 wall 타임아웃 (초). 기본 무제한(float('inf')); 유한 한도는 env로만 설정."""
        return executor_wall_seconds_from_env()
    
    @property
    def executor_memory_limit_mb(self) -> int:
        """코드 실행 메모리 제한 (MB). 0이면 제한 없음."""
        return int(os.getenv("AIMO_EXECUTOR_MEMORY_MB", "0"))
    
    # 테스트 설정
    @property
    def fast_test(self) -> bool:
        """
        빠른 테스트 모드 (``AIMO_FAST_TEST=1``): Solver가 MockSolver를 쓰고 HF 모델을 로드하지 않음.
        Mock은 문제를 풀지 않음 — 생성 코드는 ``AIMO_MOCK_GENERATED_CODE`` (기본 ``print(0)``).
        """
        return os.getenv("AIMO_FAST_TEST", "0") == "1"
    
    @property
    def refine_max_iterations(self) -> int:
        """Refine 루프 최대 반복 횟수"""
        return int(os.getenv("OMI_REFINE_MAX_ITERATIONS", "3"))
    
    @property
    def refine_enabled(self) -> bool:
        """Refine 루프 활성화 여부"""
        return os.getenv("OMI_REFINE_ENABLED", "true").lower() == "true"

    @property
    def executor_self_correction_max_attempts(self) -> int:
        """실행 실패 시 수정 코드 재시도 최대 횟수 (기본 1 = 기존 동작)"""
        return max(1, int(os.getenv("AIMO_SELF_CORRECTION_MAX_ATTEMPTS", "1")))

    @property
    def use_multi_agent_for_proof(self) -> bool:
        """proof 또는 고복잡도 문제에서 전략 루프 전에 multi-agent 선시도 (기본 False)"""
        return os.getenv("AIMO_USE_MULTI_AGENT_EARLY", "0") == "1"

    @property
    def multi_agent_early_complexity_threshold(self) -> int:
        """multi-agent 선시도 적용 복잡도 임계치 (이상이면 선시도)"""
        return int(os.getenv("AIMO_MULTI_AGENT_EARLY_COMPLEXITY_THRESHOLD", "20"))

    @property
    def use_geometric_handler(self) -> bool:
        """기하 문제 전용 핸들러 사용 (기본 False, IMO 평가 시 비활성 권장)"""
        return os.getenv("AIMO_USE_GEOMETRIC_HANDLER", "0") == "1"

    @property
    def use_llm_stage1_classifier(self) -> bool:
        """Stage1에서 LLM 분류 1회 호출 여부 (기본 False)"""
        return os.getenv("AIMO_USE_LLM_STAGE1_CLASSIFIER", "0") == "1"

    @property
    def use_knowledge_ground(self) -> bool:
        """
        Stage2 선행 지식 블록을 코드 생성 프롬프트에 넣을지 (기본 True).
        끄려면 ``OMI_DISABLE_KNOWLEDGE_GROUND=1`` (또는 ``true``/``yes``).
        """
        raw = os.getenv("OMI_DISABLE_KNOWLEDGE_GROUND", "").strip().lower()
        return raw not in ("1", "true", "yes", "on")

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
