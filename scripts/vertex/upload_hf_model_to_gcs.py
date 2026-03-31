"""
Hugging Face 모델(베이스 또는 머지 디렉터리)을 GCS에 올려 Vertex `Model.upload(artifact_uri=...)` 에 쓸 수 있게 합니다.

학습 없이 **공개 수학 모델**(예: Qwen2.5-Math-Instruct)만 올려 배포할 때 사용합니다.

예:
  # HF Hub에서 받아서 업로드 (7B 권장 — Vertex GPU는 L4/A100 등 여유 있게)
  python scripts/vertex/upload_hf_model_to_gcs.py \\
    --model-id Qwen/Qwen2.5-Math-7B-Instruct \\
    --gcs-prefix gs://BUCKET/aimo/models/hf/Qwen2.5-Math-7B-Instruct/

  # 이미 로컬에 있는 HF 루트(config.json 있는 폴더)
  python scripts/vertex/upload_hf_model_to_gcs.py \\
    --local D:/models/my-merged \\
    --gcs-prefix gs://BUCKET/aimo/models/qwen_numeric/merged/

업로드 후:
  $env:ARTIFACT_URI = "gs://.../위와 동일 경로/"
  python scripts/vertex/track_colab_vertex_smoke_seoul.py

또는 deploy_vertex_endpoint.py (리전·머신 타입 명시).

사전 검증: python scripts/vertex/verify_merged_artifact.py --local <경로>
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _parse_gcs_uri(uri: str) -> tuple[str, str]:
    u = uri.strip().rstrip("/")
    if not u.startswith("gs://"):
        raise ValueError("gcs-prefix는 gs:// 로 시작해야 합니다.")
    rest = u[5:]
    bucket, _, prefix = rest.partition("/")
    if not bucket:
        raise ValueError("버킷 이름이 비었습니다.")
    return bucket, prefix.rstrip("/") + "/" if prefix else ""


def _upload_local_tree_to_gcs(
    local_root: Path,
    bucket_name: str,
    blob_prefix: str,
    *,
    skip_existing: bool,
) -> tuple[int, int]:
    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    local_root = local_root.resolve()

    files = [p for p in local_root.rglob("*") if p.is_file()]
    uploaded = 0
    skipped = 0

    try:
        from tqdm import tqdm
    except Exception:
        tqdm = None  # type: ignore

    iterator = files
    if tqdm:
        iterator = tqdm(files, desc="gcs_upload", unit="file")

    for src in iterator:
        rel = src.relative_to(local_root).as_posix()
        name = f"{blob_prefix}{rel}" if blob_prefix else rel
        blob = bucket.blob(name)
        size = src.stat().st_size

        if skip_existing and blob.exists():
            try:
                if blob.size == size:
                    skipped += 1
                    continue
            except Exception:
                pass

        blob.upload_from_filename(str(src))
        uploaded += 1

    return uploaded, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="HF 모델 디렉터리 → GCS 업로드 (Vertex artifact)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--model-id",
        type=str,
        help="Hugging Face Hub 모델 ID (예: Qwen/Qwen2.5-Math-7B-Instruct)",
    )
    g.add_argument(
        "--local",
        type=str,
        help="config.json 이 있는 로컬 HF 디렉터리",
    )
    ap.add_argument(
        "--gcs-prefix",
        required=True,
        help="업로드 대상 gs://버킷/프리픽스/ (모델 파일이 이 프리픽스 아래에 깔림)",
    )
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="같은 크기의 blob이 이미 있으면 스킵(재시도용)",
    )
    ap.add_argument(
        "--hf-token",
        default=os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN"),
        help="게이트된 모델용 HF 토큰 (환경변수 HF_TOKEN 도 인식)",
    )
    args = ap.parse_args()

    local_root: Path
    if args.model_id:
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            print("ERROR: huggingface_hub 필요: pip install huggingface_hub", file=sys.stderr)
            return 1
        print("Downloading snapshot:", args.model_id, flush=True)
        p = snapshot_download(
            args.model_id,
            token=args.hf_token or None,
            local_files_only=False,
        )
        local_root = Path(p)
    else:
        local_root = Path(args.local).expanduser().resolve()

    if not (local_root / "config.json").is_file():
        print(f"ERROR: config.json 없음: {local_root}", file=sys.stderr)
        return 1

    try:
        bucket_name, blob_prefix = _parse_gcs_uri(args.gcs_prefix)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Local:  {local_root}")
    print(f"GCS:    gs://{bucket_name}/{blob_prefix}", flush=True)

    up, sk = _upload_local_tree_to_gcs(
        local_root,
        bucket_name,
        blob_prefix,
        skip_existing=args.skip_existing,
    )
    print(f"Done. uploaded={up}, skipped={sk}", flush=True)
    print()
    print("Vertex 배포 시 artifact_uri 예:")
    tail = args.gcs_prefix.strip().rstrip("/") + "/"
    print(f'  $env:ARTIFACT_URI = "{tail}"')
    print("  python scripts/vertex/track_colab_vertex_smoke_seoul.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())