# One-shot smoke: Vertex checks (Seoul) + Gemini once (us-central1) + endpoint ping (Seoul).
# Requires: gcloud ADC.
# 정책: 기본 실행은 Cloud Shell 등 클라우드 — run_aimo_gcp_smoke.sh 사용. 로컬 Windows는 선택.
# See docs/vertex/AIMO_GCP_PROFILE.md
$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $root

$proj = "gen-lang-client-0300734101"
$ep = "2486393813610790912"

$env:GOOGLE_CLOUD_PROJECT = $proj
$env:GOOGLE_CLOUD_LOCATION = "asia-northeast3"
$env:AIMO_VERTEX_ENDPOINT_ID = $ep

Write-Host "== run_vertex_checks (asia-northeast3) ==" -ForegroundColor Cyan
python scripts/vertex/run_vertex_checks.py --project $proj --location asia-northeast3
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== smoke_gemini_once (us-central1) ==" -ForegroundColor Cyan
$env:GOOGLE_CLOUD_LOCATION = "us-central1"
python scripts/vertex/smoke_gemini_once.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== quick_vertex_endpoint_test (asia-northeast3) ==" -ForegroundColor Cyan
$env:GOOGLE_CLOUD_LOCATION = "asia-northeast3"
$env:AIMO_VERTEX_ENDPOINT_ID = $ep
python examples/quick_vertex_endpoint_test.py
exit $LASTEXITCODE
