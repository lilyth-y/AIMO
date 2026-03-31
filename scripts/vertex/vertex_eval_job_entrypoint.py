#!/usr/bin/env python3
"""
Vertex Custom Job 컨테이너 엔트리포인트.

환경 변수:
  DATA_GCS_URI (선택): gs://bucket/path/numinamath_full.jsonl — 다운로드 후 AIMO_DATA_DIR=/data 설정
  OUTPUT_GCS_URI (선택): gs://bucket/prefix/result.jsonl — eval 종료 후 --output 파일 업로드
  OUTPUT_SUMMARY_GCS_URI (선택): gs://.../summary.json — eval 후 --write-summary-json 로 저장한 요약 업로드

나머지 인자는 eval_vertex_endpoint_quality.py 에 그대로 전달한다.
  예: python vertex_eval_job_entrypoint.py --endpoint-id ... --project ... --output /tmp/out.jsonl
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _download_gs(gs_uri: str, dest_dir: Path) -> Path:
    from google.cloud import storage

    if not gs_uri.startswith("gs://"):
        raise ValueError(f"DATA_GCS_URI must start with gs://, got {gs_uri!r}")
    rest = gs_uri[5:]
    bucket_name, _, blob = rest.partition("/")
    if not bucket_name or not blob:
        raise ValueError(f"invalid gs uri: {gs_uri!r}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    local = dest_dir / blob.split("/")[-1]
    client = storage.Client()
    client.bucket(bucket_name).blob(blob).download_to_filename(str(local))
    return local


def _upload_gs(local: Path, gs_uri: str) -> None:
    from google.cloud import storage

    if not gs_uri.startswith("gs://"):
        raise ValueError(f"OUTPUT_GCS_URI must start with gs://, got {gs_uri!r}")
    rest = gs_uri[5:]
    bucket_name, _, blob = rest.partition("/")
    if not bucket_name or not blob:
        raise ValueError(f"invalid gs uri: {gs_uri!r}")
    client = storage.Client()
    client.bucket(bucket_name).blob(blob).upload_from_filename(str(local))


def main() -> int:
    data_uri = (os.environ.get("DATA_GCS_URI") or "").strip()
    if data_uri:
        _download_gs(data_uri, Path("/data"))
        os.environ["AIMO_DATA_DIR"] = "/data"

    root = Path(__file__).resolve().parent
    eval_script = root / "eval_vertex_endpoint_quality.py"
    env = os.environ.copy()
    _pp = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = "/app/src" if not _pp else f"/app/src{os.pathsep}{_pp}"

    rc = subprocess.call([sys.executable, str(eval_script)] + sys.argv[1:], env=env)

    out_summary_gcs = (os.environ.get("OUTPUT_SUMMARY_GCS_URI") or "").strip()
    if rc == 0 and out_summary_gcs:
        args = sys.argv[1:]
        summary_path: Path | None = None
        if "--write-summary-json" in args:
            i = args.index("--write-summary-json")
            if i + 1 < len(args):
                summary_path = Path(args[i + 1])
        if summary_path is not None and summary_path.is_file():
            try:
                _upload_gs(summary_path, out_summary_gcs)
                print(f"[vertex_eval_job] uploaded summary {summary_path} -> {out_summary_gcs}", flush=True)
            except Exception as e:
                print(f"[vertex_eval_job] OUTPUT_SUMMARY_GCS_URI upload failed: {e}", file=sys.stderr, flush=True)
                return 1
        else:
            print(
                "[vertex_eval_job] OUTPUT_SUMMARY_GCS_URI set but --write-summary-json file missing; skip",
                file=sys.stderr,
                flush=True,
            )

    out_gcs = (os.environ.get("OUTPUT_GCS_URI") or "").strip()
    if rc == 0 and out_gcs:
        args = sys.argv[1:]
        out_path: Path | None = None
        if "--output" in args:
            i = args.index("--output")
            if i + 1 < len(args):
                out_path = Path(args[i + 1])
        if out_path is not None and out_path.is_file():
            try:
                _upload_gs(out_path, out_gcs)
                print(f"[vertex_eval_job] uploaded {out_path} -> {out_gcs}", flush=True)
            except Exception as e:
                print(f"[vertex_eval_job] OUTPUT_GCS_URI upload failed: {e}", file=sys.stderr, flush=True)
                return 1
        else:
            print(
                "[vertex_eval_job] OUTPUT_GCS_URI set but --output file missing or not found; skip upload",
                file=sys.stderr,
                flush=True,
            )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
