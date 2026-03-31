# Dot-source: . .\scripts\vertex\apply_aimo_gcp_env.ps1 -Profile Gemini
# See docs/vertex/AIMO_GCP_PROFILE.md
param(
    [ValidateSet('Gemini', 'Seoul')]
    [string]$Profile = 'Gemini'
)
$env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
if ($Profile -eq 'Gemini') {
    $env:GOOGLE_CLOUD_LOCATION = "us-central1"
    Remove-Item Env:AIMO_VERTEX_ENDPOINT_ID -ErrorAction SilentlyContinue
} else {
    $env:GOOGLE_CLOUD_LOCATION = "asia-northeast3"
    $env:AIMO_VERTEX_ENDPOINT_ID = "2486393813610790912"
}
