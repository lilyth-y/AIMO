# One-shot Vertex smoke: Gemini 3.1 Pro preview on the global endpoint.
# Requires: ADC or API key, Vertex AI API enabled, billing.
# Docs: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-1-pro

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

# Required for is_vertex_configured(); without this, the pipeline falls back to local HF.
if (-not $env:GOOGLE_CLOUD_PROJECT -and -not $env:GCP_PROJECT) {
    $env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
}

$env:GOOGLE_CLOUD_LOCATION = "global"
$env:VERTEX_AI_LOCATION = "global"
$env:VERTEX_AI_MODEL = "gemini-3.1-pro-preview"
if (-not $env:AIMO_MAX_NEW_TOKENS) { $env:AIMO_MAX_NEW_TOKENS = "256" }

python scripts/vertex/smoke_gemini_once.py
