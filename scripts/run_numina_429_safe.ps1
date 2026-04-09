param(
    [ValidateSet("easy", "medium", "hard")]
    [string]$DifficultyAtMost = "medium",
    [int]$MaxProblems = 30,
    [int]$Workers = 1,
    [string]$Model = "gemini-2.5-flash",
    [string]$Project = "gen-lang-client-0300734101",
    [string]$Location = "asia-northeast3",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($Workers -lt 1) {
    throw "Workers must be >= 1"
}
if ($MaxProblems -lt 1) {
    throw "MaxProblems must be >= 1"
}

# 429-minimizing preset: keep concurrency low and cap response size.
$env:PYTHONUNBUFFERED = "1"
$env:GOOGLE_CLOUD_PROJECT = $Project
$env:GOOGLE_CLOUD_LOCATION = $Location
$env:VERTEX_AI_MODEL = $Model
$env:AIMO_VERTEX_REQUEST_TIMEOUT_SEC = "45"
$env:AIMO_VERTEX_MAX_RETRIES = "0"
$env:AIMO_MAX_NEW_TOKENS = "2048"
$env:OMI_REFINE_MAX_ITERATIONS = "1"
$env:AIMO_USE_MULTI_AGENT_EARLY = "0"
$env:MAX_PROBLEMS = [string]$MaxProblems

$cmd = @(
    "python examples/run_numina_evaluation.py",
    "--data-file numinamath_full.jsonl",
    "--difficulty-at-most $DifficultyAtMost",
    "--workers $Workers"
) -join " "

Write-Host "=== 429-safe preset ==="
Write-Host "PROJECT=$($env:GOOGLE_CLOUD_PROJECT)"
Write-Host "LOCATION=$($env:GOOGLE_CLOUD_LOCATION)"
Write-Host "MODEL=$($env:VERTEX_AI_MODEL)"
Write-Host "DIFFICULTY_AT_MOST=$DifficultyAtMost"
Write-Host "MAX_PROBLEMS=$MaxProblems"
Write-Host "WORKERS=$Workers"
Write-Host "TIMEOUT_SEC=$($env:AIMO_VERTEX_REQUEST_TIMEOUT_SEC)"
Write-Host "VERTEX_RETRIES=$($env:AIMO_VERTEX_MAX_RETRIES)"
Write-Host "MAX_NEW_TOKENS=$($env:AIMO_MAX_NEW_TOKENS)"
Write-Host "REFINE_MAX_ITER=$($env:OMI_REFINE_MAX_ITERATIONS)"
Write-Host "MULTI_AGENT_EARLY=$($env:AIMO_USE_MULTI_AGENT_EARLY)"
Write-Host "Command: $cmd"

if ($DryRun) {
    Write-Host "DryRun enabled: command not executed."
    exit 0
}

Invoke-Expression $cmd
