# Numina 평가: easy만 + 저렴 설정 (비용/시간 최소화)
# 프로젝트 루트에서: .\scripts\run_numina_easy_cheap.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

# ✅ 잊지 않기: 쉬운 문제만 평가 (hard/medium 섞이는 실수 방지)
$env:EVAL_DIFFICULTY_AT_MOST = "easy"

# Easy 내부에서만 strata 통계(원하면 none으로)
if (-not $env:EVAL_EASY_STRATUM) { $env:EVAL_EASY_STRATUM = "source" }

# 비용 절감: 후보/투표/정확도 최적화 off
$env:AIMO_OPTIMIZE_ACCURACY = "0"
$env:OMI_USE_VOTING = "false"
$env:OMI_NUM_CANDIDATES = "1"

# 비용 절감: 작은 로컬 HF 모델 기본값 (원하면 밖에서 OMI_MODEL로 덮어쓰기)
if (-not $env:OMI_MODEL -and -not $env:AIMO_MODEL) { $env:OMI_MODEL = "Qwen/Qwen2.5-Math-1.5B-Instruct" }

# 안전/자원: 워커 1로 고정 (다중 프로세스는 모델 로드 중복·메모리 폭증 가능)
$env:EVAL_WORKERS = "1"
$env:AIMO_EVAL_IN_PROCESS = "1"

# 선택: 결과를 대시보드 /process에 즉시 반영하고 싶으면 1
$exportDashboard = $true

python examples/run_numina_evaluation.py --difficulty-at-most easy

Write-Host "`n결과(JSON): results\*.json"

if ($exportDashboard) {
    $latest = Get-ChildItem -Path ".\results" -Filter "*.json" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($latest) {
        python scripts/export_dashboard_process.py $latest.FullName
        Write-Host "CoT 탐색용: dashboard\public\numina_eval_balanced.json (eval 결과)"
    } else {
        Write-Host "[skip] results\*.json 없음 — numina_eval_balanced.json 은 이전 파일 유지"
    }
    # Program-Aided 패널: 항상 파이프라인 로그 기준 (eval 유무와 무관)
    python scripts/export_dashboard_from_log.py --eval-data-only --limit 30
    Write-Host "Program-Aided: dashboard\public\eval_data.json (pipeline log)"
    Write-Host "열기: http://127.0.0.1:5176/process"
}

