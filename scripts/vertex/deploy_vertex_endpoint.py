"""
Vertex Endpoint 배포 스크립트 (커스텀 서빙 컨테이너)

전제:
  - 학습 산출물(merged 모델 디렉터리)이 GCS에 존재 (artifact_uri)
  - 서빙 컨테이너 이미지가 Artifact Registry에 push 되어 있음

예:
  python scripts/vertex/deploy_vertex_endpoint.py ^
    --project gen-lang-client-0300734101 --location us-central1 ^
    --model-display-name aimo-qwen-numeric ^
    --artifact-uri gs://YOUR_BUCKET/aimo/models/qwen_numeric/merged ^
    --serving-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-serve:latest ^
    --machine-type n1-standard-4
"""

from __future__ import annotations

import argparse
import time


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--model-display-name", required=True)
    ap.add_argument("--artifact-uri", required=True, help="gs://... (merged model dir)")
    ap.add_argument("--serving-image", required=True, help="Artifact Registry image URI")

    ap.add_argument("--endpoint-display-name", default="aimo-qwen-endpoint")
    ap.add_argument("--machine-type", default="n1-standard-4")
    ap.add_argument(
        "--accelerator-type",
        default="",
        help="예: NVIDIA_TESLA_T4. 미지정 시 CPU 배포.",
    )
    ap.add_argument(
        "--accelerator-count",
        type=int,
        default=0,
        help="GPU 개수. 0이면 accelerator 비활성.",
    )
    ap.add_argument("--min-replica-count", type=int, default=1)
    ap.add_argument("--max-replica-count", type=int, default=1)
    args = ap.parse_args()

    try:
        from google.cloud import aiplatform
    except Exception as e:
        print("ERROR: google-cloud-aiplatform 미설치")
        print("  python -m pip install -r requirements-vertex-sdk.txt")
        print(f"  details: {e}")
        return 1

    aiplatform.init(project=args.project, location=args.location)

    print("Uploading Model resource...")
    model = aiplatform.Model.upload(
        display_name=args.model_display_name,
        artifact_uri=args.artifact_uri,
        serving_container_image_uri=args.serving_image,
        sync=True,
    )
    print(f"OK: model uploaded: {model.resource_name}")

    print("Creating Endpoint...")
    endpoint = aiplatform.Endpoint.create(display_name=args.endpoint_display_name, sync=True)
    print(f"OK: endpoint created: {endpoint.resource_name}")

    print("Deploying model to endpoint...")
    deploy_kwargs = {
        "model": model,
        "machine_type": args.machine_type,
        "min_replica_count": args.min_replica_count,
        "max_replica_count": args.max_replica_count,
        "sync": True,
    }
    if args.accelerator_type and args.accelerator_count > 0:
        deploy_kwargs["accelerator_type"] = args.accelerator_type
        deploy_kwargs["accelerator_count"] = args.accelerator_count
    endpoint.deploy(**deploy_kwargs)

    print("OK: deployed")
    print(f"endpoint: {endpoint.resource_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

