"""
colab-vertex-smoke_d23c1288.plan.md 를 로컬에서도 최대한 재현/트래킹하기 위한 실행 스크립트.

핵심:
  - asia-northeast3(서울)에 새 Vertex Endpoint 생성
  - smoke 모델(GCS artifact) 업로드
  - custom serving image로 배포
  - traffic_split 100% 보정
  - 즉시 predict 테스트
  - 실패 시 endpoint_id 기준으로 최근 Cloud Logging도 시도

환경변수(요약):
  - ARTIFACT_URI 또는 VERTEX_MERGED_ARTIFACT_URI: 학습·머지된 GCS 모델 경로(gs://.../merged/). 미설정 시 tiny-gpt2 스모크.
  - SMOKE_LRO_TIMEOUT_SECONDS: LRO 폴링 상한(초). none/inf/-1 이면 무제한. 미설정 시 기본 7200.
  - SMOKE_PREDICT_TIMEOUT_SECONDS: 첫 predict SDK 타임아웃(초). 미설정 시 vertex_common 기본 600(짧으면 gRPC ~60초 한도로 503).
  - SMOKE_MAX_NEW_TOKENS: 스모크 predict 의 max_new_tokens (미설정 시 기본 32, 긴 생성 시 8192 등).
  - SMOKE_VERTEX_SYNC: 1/true 이면 sync=True(기본은 sync=False + wait).
  - SMOKE_MODEL_UPLOAD_TIMEOUT_SECONDS / SMOKE_DEPLOY_TIMEOUT_SECONDS: gRPC 요청 타임아웃(선택).
  - SMOKE_STRICT_MACHINE_TYPE: 1 이면 미지원 MACHINE_TYPE 자동 교정 안 함(vertex_common).

공통 기본값·LRO 헬퍼: vertex_common.py
리전 정리(엔드포인트·모델): cleanup_vertex_region.py
답 품질 샘플 평가: eval_vertex_endpoint_quality.py
"""

from __future__ import annotations

import os
import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, Optional

# 스크립트 디렉터리를 path에 넣어 vertex_common 로드 (패키지 설치 없이 실행)
_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import (  # noqa: E402
    SmokeConfig,
    apply_smoke_env_overrides,
    vertex_lro_polling_timeout_patch,
)


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _log_append(log_path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    cfg, machine_warnings = apply_smoke_env_overrides(SmokeConfig())
    for w in machine_warnings:
        print(w, file=sys.stderr)

    # 기본 False: sync=False 후 wait() (LRO는 lro_polling_timeout으로 대기)
    use_sync = os.getenv("SMOKE_VERTEX_SYNC", "").strip().lower() in ("1", "true", "yes")
    sync_kw = use_sync

    log_path = os.getenv("SMOKE_LOG_PATH", "vertex_smoke_track2.log")
    ts = int(time.time())
    endpoint_display_name = f"{cfg.endpoint_display_name_prefix}{ts}"
    model_display_name = f"{cfg.model_display_name_prefix}{ts}"

    _log_append(
        log_path,
        {
            "event": "start",
            "ts": _now_ts(),
            "cfg": {
                "project_id": cfg.project_id,
                "location": cfg.location,
                "artifact_uri": cfg.artifact_uri,
                "serving_image_uri": cfg.serving_image_uri,
                "machine_type": cfg.machine_type,
                "accelerator_mode": cfg.accelerator_mode,
                "accelerator_type": cfg.accelerator_type if cfg.accelerator_mode != "CPU" else None,
                "accelerator_count": cfg.accelerator_count if cfg.accelerator_mode != "CPU" else None,
                "model_dir_override": cfg.model_dir_override,
                "endpoint_display_name": endpoint_display_name,
                "model_display_name": model_display_name,
                "model_upload_request_timeout_seconds": cfg.model_upload_request_timeout_seconds,
                "deploy_request_timeout_seconds": cfg.deploy_request_timeout_seconds,
                "lro_polling_timeout_seconds": cfg.lro_polling_timeout_seconds,
                "vertex_sync": use_sync,
                "machine_type_warnings": machine_warnings,
            },
        },
    )

    try:
        from google.cloud import aiplatform
        from google.cloud.aiplatform_v1.services.endpoint_service import EndpointServiceClient
        try:
            from google.cloud import logging as gcp_logging  # type: ignore
        except Exception:
            gcp_logging = None  # type: ignore
    except Exception as e:
        _log_append(log_path, {"event": "import_error", "error": str(e)})
        print(f"ERROR: 필요 패키지 import 실패: {e}")
        return 1

    aiplatform.init(project=cfg.project_id, location=cfg.location)
    _log_append(log_path, {"event": "aiplatform_init_ok", "ts": _now_ts()})

    try:
        with vertex_lro_polling_timeout_patch(lambda: cfg.lro_polling_timeout_seconds):
            _log_append(log_path, {"event": "upload_model_start", "ts": _now_ts()})
            upload_env_vars: Optional[Dict[str, str]] = None
            if cfg.model_dir_override:
                upload_env_vars = {"AIMO_MODEL_DIR": cfg.model_dir_override}

            model = aiplatform.Model.upload(
                display_name=model_display_name,
                artifact_uri=cfg.artifact_uri,
                serving_container_image_uri=cfg.serving_image_uri,
                serving_container_environment_variables=upload_env_vars,
                sync=sync_kw,
                upload_request_timeout=cfg.model_upload_request_timeout_seconds,
            )
            if not sync_kw:
                model.wait()
            _log_append(
                log_path,
                {
                    "event": "upload_model_done",
                    "ts": _now_ts(),
                    "model_resource_name": model.resource_name,
                },
            )

            _log_append(log_path, {"event": "create_endpoint_start", "ts": _now_ts()})
            endpoint = aiplatform.Endpoint.create(display_name=endpoint_display_name, sync=sync_kw)
            if not sync_kw:
                endpoint.wait()
            _log_append(
                log_path,
                {
                    "event": "create_endpoint_done",
                    "ts": _now_ts(),
                    "endpoint_resource_name": endpoint.resource_name,
                },
            )

            _log_append(log_path, {"event": "deploy_start", "ts": _now_ts()})
            deploy_kwargs: Dict[str, Any] = {
                "model": model,
                "machine_type": cfg.machine_type,
                "min_replica_count": 1,
                "max_replica_count": 1,
                "sync": sync_kw,
                "deploy_request_timeout": cfg.deploy_request_timeout_seconds,
            }
            if cfg.accelerator_mode != "CPU":
                deploy_kwargs["accelerator_type"] = cfg.accelerator_type
                deploy_kwargs["accelerator_count"] = cfg.accelerator_count
            endpoint.deploy(**deploy_kwargs)
            if not sync_kw:
                endpoint.wait()
            _log_append(log_path, {"event": "deploy_done", "ts": _now_ts()})

        client = EndpointServiceClient(client_options={"api_endpoint": f"{cfg.location}-aiplatform.googleapis.com"})
        ep = client.get_endpoint(name=endpoint.resource_name)

        endpoint_id = endpoint.resource_name.split("/")[-1]
        _log_append(log_path, {"event": "endpoint_id", "endpoint_id": endpoint_id})

        traffic_before: Optional[Dict[str, Any]] = None
        if ep.traffic_split:
            traffic_before = {k: int(v) for k, v in dict(ep.traffic_split).items()}
        _log_append(log_path, {"event": "traffic_split_before", "traffic_split": traffic_before})

        updated = False
        if not ep.traffic_split:
            dm_id: Optional[str] = None
            if ep.deployed_models:
                dm_id = ep.deployed_models[0].id

            if not dm_id:
                raise RuntimeError("deployed_models가 비어 있습니다. 배포가 완전히 끝난 뒤 다시 확인하세요.")

            for i in range(cfg.traffic_split_update_retries):
                _log_append(log_path, {"event": "traffic_split_update_attempt", "attempt": i + 1, "dm_id": dm_id})
                endpoint_obj = aiplatform.Endpoint(endpoint.resource_name)
                endpoint_obj.update(traffic_split={str(dm_id): 100})

                ep2 = client.get_endpoint(name=endpoint.resource_name)
                if ep2.traffic_split:
                    updated = True
                    traffic_after = {k: int(v) for k, v in dict(ep2.traffic_split).items()}
                    _log_append(log_path, {"event": "traffic_split_after", "traffic_split": traffic_after})
                    break

                time.sleep(cfg.traffic_split_update_sleep_seconds)

            if not updated:
                _log_append(log_path, {"event": "traffic_split_update_failed", "dm_id": dm_id})

        else:
            _log_append(log_path, {"event": "traffic_split_already_set", "traffic_split": traffic_before})

        _log_append(log_path, {"event": "predict_start", "ts": _now_ts()})
        test_endpoint = aiplatform.Endpoint(endpoint.resource_name)
        instances = [{
            "prompt": cfg.prompt,
            "max_new_tokens": cfg.max_new_tokens,
            "temperature": cfg.temperature,
        }]
        pred_timeout = cfg.predict_timeout_seconds
        response = test_endpoint.predict(
            instances=instances,
            timeout=pred_timeout if pred_timeout and pred_timeout > 0 else None,
        )
        _log_append(log_path, {"event": "predict_done", "ts": _now_ts(), "response": str(response)[:20000]})
        print(response)

        _log_append(log_path, {"event": "success", "ts": _now_ts(), "endpoint_id": endpoint_id})
        return 0

    except Exception as e:
        err_s = str(e)
        _log_append(log_path, {"event": "error", "ts": _now_ts(), "error": err_s})
        print("ERROR:", e)

        model_rn: Optional[str] = None
        endpoint_rn: Optional[str] = None
        if "model" in locals() and getattr(model, "resource_name", None):
            model_rn = model.resource_name
        if "endpoint" in locals() and getattr(endpoint, "resource_name", None):
            endpoint_rn = endpoint.resource_name

        if model_rn or endpoint_rn:
            _log_append(
                log_path,
                {
                    "event": "cleanup_hint",
                    "ts": _now_ts(),
                    "message": "Model/Endpoint가 생성된 뒤 실패한 경우 리전에 고아 리소스가 남을 수 있음.",
                    "command": "python scripts/vertex/cleanup_vertex_region.py --yes",
                    "model_resource_name": model_rn,
                    "endpoint_resource_name": endpoint_rn,
                },
            )
            print(
                "HINT: 남은 Vertex 리소스 정리 → python scripts/vertex/cleanup_vertex_region.py --yes",
                file=sys.stderr,
            )

        if "429" in err_s and "quota" in err_s.lower():
            _log_append(
                log_path,
                {
                    "event": "quota_hint",
                    "ts": _now_ts(),
                    "message": "쿼터 초과 가능. IAM & Admin → Quotas에서 CustomModelServingCPUs/GPUs 등 상향 또는 리전·머신 타입 조정.",
                },
            )
            print(
                "HINT: 쿼터(429) — GCP Console → Quotas → CustomModelServingCPUsPerProjectPerRegion 등 검토",
                file=sys.stderr,
            )

        try:
            endpoint_id = None
            if "endpoint" in locals() and getattr(endpoint, "resource_name", None):
                endpoint_id = endpoint.resource_name.split("/")[-1]
            if not endpoint_id:
                _log_append(log_path, {"event": "log_fetch_skipped", "reason": "endpoint_id_unknown"})
                return 1

            if gcp_logging is None:
                _log_append(
                    log_path,
                    {"event": "log_fetch_skipped", "reason": "google-cloud-logging not installed"},
                )
                return 1

            client = gcp_logging.Client(project=cfg.project_id)
            flt = (
                'resource.type="aiplatform.googleapis.com/Endpoint" '
                f'AND resource.labels.endpoint_id="{endpoint_id}"'
            )
            entries = client.list_entries(filter=flt, order_by=gcp_logging.DESCENDING, page_size=30)
            for e2 in entries:
                payload = e2.payload
                msg = payload.get("message") if isinstance(payload, dict) else str(payload)
                _log_append(
                    log_path,
                    {
                        "event": "gcp_log",
                        "severity": str(e2.severity),
                        "timestamp": str(e2.timestamp),
                        "message": msg[:2000],
                    },
                )
        except Exception as e2:
            _log_append(log_path, {"event": "log_fetch_failed", "error": str(e2)})

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
