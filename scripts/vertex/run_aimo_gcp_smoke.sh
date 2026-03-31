#!/usr/bin/env bash
# Cloud Shell / GCE / Linux CI — Vertex 스모크 (로컬 PC 기본 경로 아님).
# See docs/vertex/AIMO_GCP_PROFILE.md
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

proj="gen-lang-client-0300734101"
ep="2486393813610790912"
export GOOGLE_CLOUD_PROJECT="$proj"
export GOOGLE_CLOUD_LOCATION="asia-northeast3"
export AIMO_VERTEX_ENDPOINT_ID="$ep"

echo "== run_vertex_checks (asia-northeast3) =="
python scripts/vertex/run_vertex_checks.py --project "$proj" --location asia-northeast3

echo "== smoke_gemini_once (us-central1) =="
export GOOGLE_CLOUD_LOCATION="us-central1"
python scripts/vertex/smoke_gemini_once.py

echo "== quick_vertex_endpoint_test (asia-northeast3) =="
export GOOGLE_CLOUD_LOCATION="asia-northeast3"
export AIMO_VERTEX_ENDPOINT_ID="$ep"
python examples/quick_vertex_endpoint_test.py

echo "OK: run_aimo_gcp_smoke.sh finished"
