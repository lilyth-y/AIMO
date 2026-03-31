# Numina 60문항 전체 평가 (벤치마크)
# 프로젝트 루트에서: .\scripts\run_numina_60.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

# MAX_PROBLEMS 없음 = 60문항 전체
if ($env:MAX_PROBLEMS) { Remove-Item Env:MAX_PROBLEMS }
python examples/run_numina_evaluation.py

Write-Host "`n결과: results\numina_balanced_results.json"
Write-Host "그라디언트: results\gradient_report_numina*.json"
