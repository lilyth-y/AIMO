# Numina: first 30 rows from numinamath_full.jsonl with difficulty-at-most medium, Vertex Gemini 3.1 (global).
# Results -> $AIMO_RESULTS_DIR\results\ (default: repo \_eval_gemini31_m30\results) so main results/ is not overwritten.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot

if (-not $env:GOOGLE_CLOUD_PROJECT -and -not $env:GCP_PROJECT) {
    $env:GOOGLE_CLOUD_PROJECT = "gen-lang-client-0300734101"
}
$env:GOOGLE_CLOUD_LOCATION = "global"
$env:VERTEX_AI_LOCATION = "global"
$env:VERTEX_AI_MODEL = "gemini-3.1-pro-preview"
$env:MAX_PROBLEMS = "30"
$env:EVAL_WORKERS = "1"
if (-not $env:AIMO_RESULTS_DIR) {
    $env:AIMO_RESULTS_DIR = Join-Path $RepoRoot "_eval_gemini31_m30"
}
if (-not $env:AIMO_MAX_NEW_TOKENS) { $env:AIMO_MAX_NEW_TOKENS = "8192" }
if (-not $env:AIMO_VERTEX_MAX_RETRIES) { $env:AIMO_VERTEX_MAX_RETRIES = "3" }

New-Item -ItemType Directory -Force -Path (Join-Path $env:AIMO_RESULTS_DIR "results") | Out-Null

$log = Join-Path $env:AIMO_RESULTS_DIR "run_console.log"
python -u examples/run_numina_evaluation.py --data-file numinamath_full.jsonl --difficulty-at-most medium --workers 1 2>&1 | Tee-Object -FilePath $log
