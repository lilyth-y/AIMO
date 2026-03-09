"""Pipeline configuration flags (lightweight).
Adjust here instead of scattering magic numbers.

Note: 새로운 코드는 settings.py의 Settings 클래스를 사용하는 것을 권장합니다.
이 파일은 하위 호환성을 위해 유지됩니다.
"""

# 하위 호환성을 위한 설정 import
try:
    from .settings import settings
    
    # Settings에서 값 가져오기
    USE_STRUCTURED = settings.use_structured
    STRUCTURED_LENGTH_THRESHOLD = settings.structured_length_threshold
    COMPLEXITY_STRUCTURED_MIN_SCORE = settings.complexity_structured_min_score
    LOG_PATH = str(settings.log_path)
    NUM_CANDIDATES = settings.num_candidates
    USE_VOTING = settings.use_voting
    HF_MODEL_NAME = settings.model_name
    QUANTIZATION_DEFAULT = settings.quantization
    DECOMPOSITION_COMPLEXITY_THRESHOLD = settings.decomposition_complexity_threshold
except ImportError:
    # Fallback to old values if settings.py not available (repo_id only, no local path)
    USE_STRUCTURED = True
    STRUCTURED_LENGTH_THRESHOLD = 120
    COMPLEXITY_STRUCTURED_MIN_SCORE = 5
    LOG_PATH = "logs/eval_log.jsonl"
    NUM_CANDIDATES = 3
    USE_VOTING = False
    HF_MODEL_NAME = "MathLLMs/MathCoder-L-13B"
    QUANTIZATION_DEFAULT = "8bit"
    DECOMPOSITION_COMPLEXITY_THRESHOLD = 15

# Legacy constants (deprecated)
REFINE_PASSES = 0  # future use
CANDIDATE_TEMPS = [0.2, 0.7, 1.0]
