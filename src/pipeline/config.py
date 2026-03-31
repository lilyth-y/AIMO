"""Pipeline configuration flags (lightweight).
Adjust here instead of scattering magic numbers.

Note: 새로운 코드는 settings.py의 Settings 클래스를 사용하는 것을 권장합니다.
이 파일은 하위 호환성을 위해 유지됩니다.

동기화: 아래 이름들은 import 시점 스냅샷이 아니라, 접근할 때마다
`settings`의 동일 항목을 읽습니다(환경 변수 변경 반영). `config.X = 값`으로
모듈에 직접 대입하면 그 값이 우선합니다.
"""

from __future__ import annotations

try:
    from .settings import settings as _settings
    _SETTINGS_OK = True
except ImportError:
    _settings = None
    _SETTINGS_OK = False

# settings 속성명 → (없으면 fallback에서만 사용)
_SYNC_MAP: dict[str, str | None] = {
    "USE_STRUCTURED": "use_structured",
    "STRUCTURED_LENGTH_THRESHOLD": "structured_length_threshold",
    "COMPLEXITY_STRUCTURED_MIN_SCORE": "complexity_structured_min_score",
    "LOG_PATH": "log_path",
    "NUM_CANDIDATES": "num_candidates",
    "USE_VOTING": "use_voting",
    "HF_MODEL_NAME": "model_name",
    "QUANTIZATION_DEFAULT": "quantization",
    "DECOMPOSITION_COMPLEXITY_THRESHOLD": "decomposition_complexity_threshold",
    "EXECUTOR_SELF_CORRECTION_MAX_ATTEMPTS": "executor_self_correction_max_attempts",
    "USE_MULTI_AGENT_EARLY": "use_multi_agent_for_proof",
    "MULTI_AGENT_EARLY_COMPLEXITY_THRESHOLD": "multi_agent_early_complexity_threshold",
    "USE_GEOMETRIC_HANDLER": "use_geometric_handler",
    "USE_LLM_STAGE1_CLASSIFIER": "use_llm_stage1_classifier",
}

_FALLBACK = {
    "USE_STRUCTURED": True,
    "STRUCTURED_LENGTH_THRESHOLD": 120,
    "COMPLEXITY_STRUCTURED_MIN_SCORE": 5,
    "LOG_PATH": "logs/eval_log.jsonl",
    "NUM_CANDIDATES": 3,
    "USE_VOTING": False,
    "HF_MODEL_NAME": "Qwen/Qwen2.5-Math-7B-Instruct",
    "QUANTIZATION_DEFAULT": "4bit",
    "DECOMPOSITION_COMPLEXITY_THRESHOLD": 15,
    "EXECUTOR_SELF_CORRECTION_MAX_ATTEMPTS": 1,
    "USE_MULTI_AGENT_EARLY": False,
    "MULTI_AGENT_EARLY_COMPLEXITY_THRESHOLD": 20,
    "USE_GEOMETRIC_HANDLER": False,
    "USE_LLM_STAGE1_CLASSIFIER": False,
}


def _synced_value(name: str):
    if _SETTINGS_OK and _settings is not None:
        prop = _SYNC_MAP[name]
        val = getattr(_settings, prop)
        if name == "LOG_PATH":
            return str(val)
        return val
    return _FALLBACK[name]


def __getattr__(name: str):
    if name in _SYNC_MAP:
        return _synced_value(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    base = {k for k in globals().keys() if not k.startswith("_")}
    return sorted(base | set(_SYNC_MAP.keys()))


# Legacy constants (deprecated)
REFINE_PASSES = 0  # future use
CANDIDATE_TEMPS = [0.2, 0.7, 1.0]

__all__ = [
    *sorted(_SYNC_MAP.keys()),
    "REFINE_PASSES",
    "CANDIDATE_TEMPS",
]
