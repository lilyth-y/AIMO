"""
Vertex AI 환경 체크 (CLI/SDK 연결 확인)

실행:
  python scripts/vertex/vertex_env_check.py --project gen-lang-client-0300734101 --location us-central1
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_VDIR = Path(__file__).resolve().parent
if str(_VDIR) not in sys.path:
    sys.path.insert(0, str(_VDIR))

from vertex_common import resolve_location, resolve_project_id  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=str, default=resolve_project_id(prefer_cleanup_alias=False))
    ap.add_argument("--location", type=str, default=resolve_location())
    args = ap.parse_args()

    try:
        from google.cloud import aiplatform
    except Exception as e:
        print("ERROR: google-cloud-aiplatform 미설치")
        print("  python -m pip install -r requirements-vertex-sdk.txt")
        print(f"  details: {e}")
        return 1

    try:
        aiplatform.init(project=args.project, location=args.location)
        # Lightweight API call: list endpoints (SDK 1.70+ no longer supports page_size on list())
        _ = aiplatform.Endpoint.list(
            order_by="create_time desc",
            project=args.project,
            location=args.location,
        )
        print("OK: Vertex SDK 연결 성공")
        print(f"  project:  {args.project}")
        print(f"  location: {args.location}")
        return 0
    except Exception as e:
        print("ERROR: Vertex SDK 연결 실패")
        print("  1) gcloud auth login")
        print("  2) gcloud auth application-default login")
        print("  3) gcloud services enable aiplatform.googleapis.com")
        print(f"  details: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

