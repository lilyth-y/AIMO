"""
Vertex 스모크·정리 스크립트 공통: 기본값, 환경 해석, gcloud 헬퍼, LRO 폴링 보정.

환경변수(공통 우선순위):
  PROJECT_ID → GOOGLE_CLOUD_PROJECT → VERTEX_CLEANUP_PROJECT_ID → 기본값.
  LOCATION → GOOGLE_CLOUD_LOCATION → VERTEX_CLEANUP_LOCATION → 기본값.

환경변수(추가):
  SMOKE_STRICT_MACHINE_TYPE=1 — 알려진 미지원 MACHINE_TYPE 을 자동 교정하지 않음(디버그용).
  ARTIFACT_URI — GCS 모델 프리픽스 (최우선).
  VERTEX_MERGED_ARTIFACT_URI — 학습·머지 산출물 gs://.../merged/ (ARTIFACT_URI 미설정 시 사용).

다른 도구에서 재사용할 때는 이 모듈만 import 하면 됨.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

# --- 프로젝트·리전 (한곳에서만 수정) ---
DEFAULT_VERTEX_PROJECT_ID = "gen-lang-client-0300734101"
DEFAULT_VERTEX_LOCATION = "asia-northeast3"

# 스모크 트래킹(track_*) 기본값 (tiny-gpt2 — 인프라 검증용)
DEFAULT_SMOKE_ARTIFACT_URI = (
    "gs://gen-lang-client-0300734101-aimo-vertex-341687483990/aimo/models/smoke/tiny-gpt2/"
)
# 학습·머지 완료 후 실제 배포 시 GCS 경로 예시 (버킷/작업명은 학습 산출물에 맞게 교체)
# Vertex CustomJob + --save-merged → gs://.../merged/ 아래에 HF 호환 디렉터리
EXAMPLE_MERGED_ARTIFACT_URI = "gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged/"
DEFAULT_SERVING_IMAGE_URI = (
    "us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest"
)

# 정리(cleanup_*) 기본: displayName prefix
DEFAULT_CLEANUP_DISPLAY_NAME_PREFIX = "aimo-"

# 온라인 추론 CPU 표에 없는 등, 관측·문서 기반으로 거절되는 타입 (소문자로 비교)
INVALID_VERTEX_PREDICTION_MACHINE_TYPES = frozenset({"n1-standard-1"})
# N1 계열 최소 허용(공식 configure-compute CPU 표 기준)
VERTEX_PREDICTION_N1_MINIMUM = "n1-standard-2"


def resolve_project_id(*, prefer_cleanup_alias: bool = False) -> str:
    """Vertex 스크립트 공통 프로젝트 우선순위."""
    if prefer_cleanup_alias:
        return (
            os.getenv("VERTEX_CLEANUP_PROJECT_ID")
            or os.getenv("PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or DEFAULT_VERTEX_PROJECT_ID
        )
    return (
        os.getenv("PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("VERTEX_CLEANUP_PROJECT_ID")
        or DEFAULT_VERTEX_PROJECT_ID
    )


def resolve_location() -> str:
    """Vertex 스크립트 공통 리전 우선순위."""
    return (
        os.getenv("LOCATION")
        or os.getenv("GOOGLE_CLOUD_LOCATION")
        or os.getenv("VERTEX_CLEANUP_LOCATION")
        or DEFAULT_VERTEX_LOCATION
    )


def resolve_project_id_for_cleanup() -> str:
    """정리 스크립트에서만 cleanup alias를 최우선으로 사용."""
    return (
        os.getenv("VERTEX_CLEANUP_PROJECT_ID")
            or os.getenv("PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or DEFAULT_VERTEX_PROJECT_ID
        )


def resolve_location_for_cleanup() -> str:
    """정리 스크립트에서만 cleanup alias를 최우선으로 사용."""
    return (
        os.getenv("VERTEX_CLEANUP_LOCATION")
        or os.getenv("LOCATION")
        or os.getenv("GOOGLE_CLOUD_LOCATION")
        or DEFAULT_VERTEX_LOCATION
    )


def find_gcloud() -> str:
    path = shutil.which("gcloud")
    if path:
        return path
    win = os.path.join(
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        "Google",
        "Cloud SDK",
        "google-cloud-sdk",
        "bin",
        "gcloud.cmd",
    )
    if os.path.isfile(win):
        return win
    raise FileNotFoundError(
        "gcloud 를 찾을 수 없습니다. Google Cloud SDK 설치 후 PATH 에 추가하세요."
    )


def gcloud_json(gcloud: str, args: Sequence[str]) -> Any:
    r = subprocess.run(
        [gcloud, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout or "")
        raise subprocess.CalledProcessError(r.returncode, [gcloud, *args])
    return json.loads(r.stdout)


def filter_display_name_prefix(
    items: List[Dict[str, Any]],
    prefix: Optional[str],
) -> List[Dict[str, Any]]:
    if not prefix:
        return items
    return [x for x in items if str(x.get("displayName", "")).startswith(prefix)]


def parse_lro_timeout_seconds(raw: str) -> Optional[float]:
    """none/inf/-1 -> 무제한(None), 그 외 float(초)."""
    t = raw.strip().lower()
    if t in ("none", "inf", "-1"):
        return None
    return float(raw)


@contextmanager
def vertex_lro_polling_timeout_patch(
    resolve_timeout: Callable[[], Optional[float]],
) -> Iterator[None]:
    """google.api_core LRO 기본 폴링(900초)을 덮어쓴다."""
    from google.api_core.future import polling as polling_mod

    _default_marker = polling_mod.PollingFuture._DEFAULT_VALUE
    _orig = polling_mod.PollingFuture.result

    def _patched(
        self: Any,
        timeout: Any = _default_marker,
        retry: Any = None,
        polling: Any = None,
    ) -> Any:
        if timeout is _default_marker:
            timeout = resolve_timeout()
        return _orig(self, timeout=timeout, retry=retry, polling=polling)

    polling_mod.PollingFuture.result = _patched  # type: ignore[method-assign]
    try:
        yield
    finally:
        polling_mod.PollingFuture.result = _orig  # type: ignore[method-assign]


@dataclass
class SmokeConfig:
    """서울 스모크 트래킹용 설정. 기본값은 vertex_common 상수와 동기."""

    project_id: str = DEFAULT_VERTEX_PROJECT_ID
    location: str = DEFAULT_VERTEX_LOCATION
    artifact_uri: str = DEFAULT_SMOKE_ARTIFACT_URI
    serving_image_uri: str = DEFAULT_SERVING_IMAGE_URI

    # 온라인 추론(커스텀 모델) CPU machine type은 공식 표에 n1-standard-2부터 나열됨.
    # n1-standard-1 은 Vertex AI 예측용 CPU 목록에 없어 API 400 이 날 수 있음.
    # https://cloud.google.com/vertex-ai/docs/predictions/configure-compute
    machine_type: str = "n1-standard-4"
    accelerator_type: str = "NVIDIA_TESLA_T4"
    accelerator_count: int = 1
    accelerator_mode: str = "T4"
    model_dir_override: Optional[str] = None

    prompt: str = "What is 2+2? Reply with one number only."
    max_new_tokens: int = 32
    temperature: float = 0.0

    endpoint_display_name_prefix: str = "aimo-endpoint-seoul-smoke-redeploy-"
    model_display_name_prefix: str = "aimo-smoke-tiny-gpt2-model-"

    traffic_split_update_retries: int = 5
    traffic_split_update_sleep_seconds: float = 3.0

    model_upload_request_timeout_seconds: Optional[float] = None
    deploy_request_timeout_seconds: Optional[float] = None
    lro_polling_timeout_seconds: Optional[float] = 7200.0
    # 첫 predict 시 GCS→디스크 다운로드+GPU 로드로 60초를 넘길 수 있음 (SDK 기본 상한)
    # eval_vertex_endpoint_quality 기본(600s)과 맞춤; 필요 시 SMOKE_PREDICT_TIMEOUT_SECONDS 로 덮어쓴다.
    predict_timeout_seconds: Optional[float] = 600.0


def _normalize_smoke_machine_type(cfg: SmokeConfig) -> List[str]:
    """문서·실측에서 400이 나는 machine_type을 최소 허용값으로 교정. 경고 문구 목록 반환."""
    if os.getenv("SMOKE_STRICT_MACHINE_TYPE", "").strip().lower() in ("1", "true", "yes"):
        return []

    mt_key = (cfg.machine_type or "").strip().lower()
    if mt_key not in INVALID_VERTEX_PREDICTION_MACHINE_TYPES:
        return []

    old = cfg.machine_type
    cfg.machine_type = VERTEX_PREDICTION_N1_MINIMUM

    return [
        (
            f"[vertex_common] machine_type={old!r} 은 Vertex online prediction 허용 목록에 없어 "
            f"{cfg.machine_type!r} 로 교정했습니다. "
            f"(SMOKE_STRICT_MACHINE_TYPE=1 이면 교정 안 함) "
            f"https://cloud.google.com/vertex-ai/docs/predictions/configure-compute"
        )
    ]


def apply_smoke_env_overrides(cfg: SmokeConfig) -> Tuple[SmokeConfig, List[str]]:
    """환경변수로 SmokeConfig 덮어쓰기(track 스크립트용). 두 번째 값은 stderr에 출력할 경고 목록."""
    cfg.project_id = resolve_project_id(prefer_cleanup_alias=False)
    cfg.location = resolve_location()
    art_explicit = os.getenv("ARTIFACT_URI", "").strip()
    art_merged = os.getenv("VERTEX_MERGED_ARTIFACT_URI", "").strip()
    if art_explicit:
        cfg.artifact_uri = art_explicit
    elif art_merged:
        cfg.artifact_uri = art_merged.rstrip("/") + "/"
    else:
        pass  # DEFAULT_SMOKE_ARTIFACT_URI (tiny 스모크)
    cfg.serving_image_uri = os.getenv("SERVING_IMAGE_URI", cfg.serving_image_uri)
    cfg.machine_type = os.getenv("MACHINE_TYPE", cfg.machine_type)
    cfg.accelerator_mode = os.getenv("SMOKE_ACCELERATOR_MODE", cfg.accelerator_mode)
    model_dir_override = os.getenv("SMOKE_MODEL_DIR_OVERRIDE")
    cfg.model_dir_override = model_dir_override if model_dir_override and model_dir_override.strip() else None

    mt = os.getenv("SMOKE_MODEL_UPLOAD_TIMEOUT_SECONDS", "").strip()
    cfg.model_upload_request_timeout_seconds = float(mt) if mt else None

    dt = os.getenv("SMOKE_DEPLOY_TIMEOUT_SECONDS", "").strip()
    cfg.deploy_request_timeout_seconds = float(dt) if dt else None

    lro_raw = os.getenv("SMOKE_LRO_TIMEOUT_SECONDS")
    if lro_raw is not None and str(lro_raw).strip():
        cfg.lro_polling_timeout_seconds = parse_lro_timeout_seconds(str(lro_raw))

    pt = os.getenv("SMOKE_PREDICT_TIMEOUT_SECONDS", "").strip()
    if pt:
        cfg.predict_timeout_seconds = float(pt)

    mnt = os.getenv("SMOKE_MAX_NEW_TOKENS", "").strip()
    if mnt:
        cfg.max_new_tokens = int(mnt)

    warnings = _normalize_smoke_machine_type(cfg)
    return cfg, warnings
