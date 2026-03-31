"""
Vertex Custom Training Job 제출 (Qwen QLoRA SFT)

사전 준비:
  - gcloud auth login / application-default login
  - aiplatform API enabled
  - 학습 컨테이너 이미지를 Artifact Registry에 push
  - train/dev jsonl을 GCS에 업로드

실행 예:
  python scripts/vertex/submit_vertex_custom_job.py ^
    --project gen-lang-client-0300734101 --location asia-northeast3 ^
    --container-image us-central1-docker.pkg.dev/gen-lang-client-0300734101/aimo/vertex-train:latest ^
    --train-gcs gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/train.jsonl ^
    --dev-gcs gs://YOUR_BUCKET/aimo/finetune/qwen_numeric/dev.jsonl ^
    --gcs-output gs://YOUR_BUCKET/aimo/models/qwen_numeric ^
    --base-model Qwen/Qwen2.5-Math-7B-Instruct
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List
from urllib.parse import urlparse

_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import resolve_location  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument(
        "--location",
        default=resolve_location(),
        help="기본: vertex_common.resolve_location() (env LOCATION / GOOGLE_CLOUD_LOCATION 등)",
    )

    ap.add_argument("--container-image", required=True, help="Artifact Registry image URI")
    ap.add_argument("--train-gcs", required=True, help="gs://... train.jsonl")
    ap.add_argument("--dev-gcs", required=True, help="gs://... dev.jsonl")
    ap.add_argument("--gcs-output", required=True, help="gs://... output prefix")
    ap.add_argument(
        "--staging-bucket",
        default="",
        help="gs://... (미지정 시 --gcs-output의 버킷을 사용)",
    )

    ap.add_argument("--base-model", default="Qwen/Qwen2.5-Math-7B-Instruct")
    ap.add_argument("--job-display-name", default="aimo-qwen-qlora-sft")
    ap.add_argument("--machine-type", default="n1-standard-8")
    ap.add_argument(
        "--accelerator-type",
        default="NVIDIA_TESLA_A100",
        help="예: NVIDIA_TESLA_T4, NVIDIA_L4, NVIDIA_TESLA_A100. 비우거나 --accelerator-count 0이면 GPU 미사용",
    )
    ap.add_argument("--accelerator-count", type=int, default=1, help="0이면 GPU 미사용")
    ap.add_argument("--replica-count", type=int, default=1)

    # Train args
    ap.add_argument("--max-seq-len", type=int, default=2048)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--save-merged", action="store_true")
    args = ap.parse_args()

    try:
        from google.cloud import aiplatform
    except Exception as e:
        print("ERROR: google-cloud-aiplatform 미설치")
        print("  python -m pip install -r requirements-vertex-sdk.txt")
        print(f"  details: {e}")
        return 1

    staging_bucket = (args.staging_bucket or "").strip()
    if not staging_bucket:
        parsed = urlparse(args.gcs_output)
        if parsed.scheme == "gs" and parsed.netloc:
            staging_bucket = f"gs://{parsed.netloc}"

    if staging_bucket:
        aiplatform.init(project=args.project, location=args.location, staging_bucket=staging_bucket)
    else:
        aiplatform.init(project=args.project, location=args.location)

    # The container ENTRYPOINT is train_qlora_sft.py, so args are passed directly.
    cmd_args: List[str] = [
        "--base_model",
        args.base_model,
        "--train_jsonl",
        args.train_gcs,
        "--dev_jsonl",
        args.dev_gcs,
        "--output_dir",
        "/tmp/output",
        "--max_seq_len",
        str(args.max_seq_len),
        "--epochs",
        str(args.epochs),
        "--lr",
        str(args.lr),
        "--batch_size",
        str(args.batch_size),
        "--grad_accum",
        str(args.grad_accum),
        "--gcs_output",
        args.gcs_output,
    ]
    if args.save_merged:
        cmd_args.append("--save_merged")

    job = aiplatform.CustomContainerTrainingJob(
        display_name=args.job_display_name,
        container_uri=args.container_image,
    )

    print("Submitting Custom Training Job...")
    run_kwargs = dict(
        replica_count=args.replica_count,
        machine_type=args.machine_type,
        args=cmd_args,
        base_output_dir=args.gcs_output,  # job outputs/logs
        sync=False,
    )

    accel_type = (args.accelerator_type or "").strip()
    accel_count = int(args.accelerator_count)
    if accel_count > 0 and accel_type:
        run_kwargs["accelerator_type"] = accel_type
        run_kwargs["accelerator_count"] = accel_count

    model = job.run(**run_kwargs)

    print("OK: job submitted (async)")
    print("Check in GCP Console: Vertex AI -> Training -> Custom jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

