"""
Vertex Custom Job으로 `eval_vertex_endpoint_quality.py` 실행 (평가 프로세스를 GCP에서 수행).

추론은 이미 배포된 Vertex **Online Prediction 엔드포인트**에 predict (로컬 7B 로드 없음).
이 컨테이너는 CPU로 API 호출·채점만 수행 (GPU 불필요).

사전 준비:
  - Artifact Registry에 vertex-eval 이미지 push (`docker/vertex-eval/Dockerfile`)
  - Numina JSONL이 크면 GCS에 업로드 후 `--gcs-data-uri` 로 전달 (컨테이너가 /data 로 받음)
  - Vertex API 활성화, gcloud auth application-default login

실행 예:
  python scripts/vertex/submit_vertex_eval_job.py ^
    --project YOUR_PROJECT --location asia-northeast3 ^
    --container-image asia-northeast3-docker.pkg.dev/YOUR_PROJECT/aimo/vertex-eval:latest ^
    --staging-bucket gs://YOUR_BUCKET/vertex-staging ^
    --endpoint-id 1234567890123456789 ^
    --gcs-data-uri gs://YOUR_BUCKET/aimo/data/numinamath_full.jsonl ^
    --gcs-output-uri gs://YOUR_BUCKET/aimo/results/vertex_eval_run.jsonl ^
    --gcs-summary-uri gs://YOUR_BUCKET/aimo/results/vertex_summary.json ^
    --write-summary-json /tmp/vertex_summary.json ^
    --enforce-ralph-accuracy ^
    --n-problems 200 --data-file numinamath_full.jsonl --difficulty-at-most medium

Ralph 80% 목표·게이트: docs/run-eval/RALPH_VERTEX.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import resolve_location, resolve_project_id  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Submit Vertex Custom Job for endpoint quality eval")
    ap.add_argument("--project", default=resolve_project_id(prefer_cleanup_alias=False))
    ap.add_argument("--location", default=resolve_location())
    ap.add_argument("--container-image", required=True, help="Artifact Registry image URI (vertex-eval)")
    ap.add_argument(
        "--staging-bucket",
        required=True,
        help="gs://bucket/prefix — aiplatform.init staging (Custom Job 로그/아티팩트)",
    )
    ap.add_argument("--endpoint-id", required=True, help="Vertex Endpoint ID (숫자 또는 전체 리소스 이름)")
    ap.add_argument("--job-display-name", default="aimo-vertex-endpoint-eval")

    ap.add_argument(
        "--gcs-data-uri",
        default="",
        help="선택: gs://.../numinamath_full.jsonl — 컨테이너가 다운로드해 AIMO_DATA_DIR=/data",
    )
    ap.add_argument(
        "--gcs-output-uri",
        default="",
        help="선택: gs://.../vertex_eval.jsonl — eval 완료 후 로컬 --output 파일 업로드",
    )
    ap.add_argument(
        "--gcs-summary-uri",
        default="",
        help="선택: gs://.../vertex_summary.json — eval 후 --write-summary-json 파일 업로드 (OUTPUT_SUMMARY_GCS_URI)",
    )

    ap.add_argument("--n-problems", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--data-file", default="numinamath_full.jsonl")
    ap.add_argument("--difficulty-at-most", choices=("easy", "medium", "hard"), default=None)
    ap.add_argument("--sources", default="", help="쉼표 구분 소스 허용 목록 (비우면 전체)")

    ap.add_argument("--machine-type", default="e2-standard-4", help="CPU만 사용; GPU 불필요")
    ap.add_argument("--replica-count", type=int, default=1)

    ap.add_argument(
        "--predict-timeout",
        type=float,
        default=float(os.getenv("VERTEX_PREDICT_TIMEOUT_SECONDS", "600")),
        help="엔드포인트 predict 타임아웃(초). 기본 600; 상한은 eval의 VERTEX_PREDICT_TIMEOUT_MAX. env: VERTEX_PREDICT_TIMEOUT_SECONDS",
    )
    ap.add_argument(
        "--max-new-tokens",
        type=int,
        default=int(os.getenv("VERTEX_MAX_NEW_TOKENS", "2048")),
        help="생성 토큰 상한(서빙으로 전달). 길면 503 빈발 시 낮춤. 기본 2048. env: VERTEX_MAX_NEW_TOKENS",
    )
    ap.add_argument(
        "--vertex-predict-retries",
        type=int,
        default=int(os.getenv("VERTEX_PREDICT_TRANSIENT_RETRIES", "3")),
        help="503 등 일시 오류 시 predict 재시도 횟수. env: VERTEX_PREDICT_TRANSIENT_RETRIES",
    )
    ap.add_argument(
        "--vertex-predict-retry-delay",
        type=float,
        default=float(os.getenv("VERTEX_PREDICT_RETRY_DELAY", "5")),
        help="재시도 전 대기(초), 선형 증가. env: VERTEX_PREDICT_RETRY_DELAY",
    )
    ap.add_argument(
        "--max-format-retries",
        type=int,
        default=int(os.getenv("VERTEX_MAX_FORMAT_RETRIES", "3")),
        help="<ANS> strict 불통과 시 추가 생성 횟수. eval과 동일. env: VERTEX_MAX_FORMAT_RETRIES",
    )
    ap.add_argument(
        "--verify-max-new-tokens",
        type=int,
        default=int(os.getenv("VERTEX_VERIFY_MAX_NEW_TOKENS", "1024")),
        help="검수(verify) Agent 생성 토큰 상한. eval --verify-max-new-tokens 와 동일. env: VERTEX_VERIFY_MAX_NEW_TOKENS",
    )
    ap.add_argument(
        "--service-account",
        default="",
        help="선택: Custom Job 실행 서비스 계정 이메일",
    )
    ap.add_argument(
        "--enforce-ralph-accuracy",
        action="store_true",
        help="컨테이너에 --enforce-ralph-accuracy 전달 (기본 80% 목표, env AIMO_RALPH_TARGET_ACCURACY_PCT)",
    )
    ap.add_argument(
        "--write-summary-json",
        default="",
        help="컨테이너 내 요약 JSON 경로 (예: /tmp/vertex_summary.json). 로그/아티팩트로 내려받아 ralph_vertex_accuracy_gate 실행.",
    )
    args = ap.parse_args()

    try:
        from google.cloud import aiplatform
    except Exception as e:
        print("ERROR: google-cloud-aiplatform 필요:", e, file=sys.stderr)
        print("  pip install -r requirements-vertex-sdk.txt", file=sys.stderr)
        return 1

    staging = args.staging_bucket.strip()
    if not staging.startswith("gs://"):
        print("ERROR: --staging-bucket must be gs://...", file=sys.stderr)
        return 1

    out_local = "/tmp/vertex_eval_job.jsonl"

    cmd_args: List[str] = [
        "--endpoint-id",
        str(args.endpoint_id),
        "--project",
        args.project,
        "--location",
        args.location,
        "--n-problems",
        str(args.n_problems),
        "--seed",
        str(args.seed),
        "--data-file",
        args.data_file,
        "--output",
        out_local,
        "--predict-timeout",
        str(args.predict_timeout),
        "--max-new-tokens",
        str(args.max_new_tokens),
        "--vertex-predict-retries",
        str(args.vertex_predict_retries),
        "--vertex-predict-retry-delay",
        str(args.vertex_predict_retry_delay),
        "--max-format-retries",
        str(args.max_format_retries),
        "--verify-max-new-tokens",
        str(args.verify_max_new_tokens),
    ]
    if args.difficulty_at_most:
        cmd_args.extend(["--difficulty-at-most", args.difficulty_at_most])
    if (args.sources or "").strip():
        cmd_args.extend(["--sources", args.sources.strip()])
    if args.enforce_ralph_accuracy:
        cmd_args.append("--enforce-ralph-accuracy")
    wj = (args.write_summary_json or "").strip()
    if wj:
        cmd_args.extend(["--write-summary-json", wj])

    env_list: List[Dict[str, str]] = []
    gcs_data = (args.gcs_data_uri or "").strip()
    if gcs_data:
        env_list.append({"name": "DATA_GCS_URI", "value": gcs_data})
    gcs_out = (args.gcs_output_uri or "").strip()
    if gcs_out:
        env_list.append({"name": "OUTPUT_GCS_URI", "value": gcs_out})
    gcs_summary = (args.gcs_summary_uri or "").strip()
    if gcs_summary:
        env_list.append({"name": "OUTPUT_SUMMARY_GCS_URI", "value": gcs_summary})

    worker_pool_specs: List[Dict[str, Any]] = [
        {
            "machine_spec": {"machine_type": args.machine_type},
            "replica_count": args.replica_count,
            "container_spec": {
                "image_uri": args.container_image,
                "command": ["python3", "/app/scripts/vertex/vertex_eval_job_entrypoint.py"],
                "args": cmd_args,
                "env": env_list,
            },
        }
    ]

    aiplatform.init(project=args.project, location=args.location, staging_bucket=staging)

    job = aiplatform.CustomJob(
        display_name=args.job_display_name,
        worker_pool_specs=worker_pool_specs,
        project=args.project,
        location=args.location,
        staging_bucket=staging,
    )

    print("Submitting Vertex Custom Job (eval_vertex_endpoint_quality)...")
    sa = (args.service_account or "").strip()
    if sa:
        job.submit(service_account=sa)
    else:
        job.submit()

    print("OK: Custom Job submitted (async)")
    print("Console: Vertex AI -> Training -> Custom jobs")
    if job.resource_name:
        print("Resource:", job.resource_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
