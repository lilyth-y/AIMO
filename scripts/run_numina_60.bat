@echo off
REM Numina 60문항 전체 평가 (벤치마크)
REM 프로젝트 루트에서: scripts\run_numina_60.bat
cd /d "%~dp0\.."
set MAX_PROBLEMS=
python examples/run_numina_evaluation.py
echo.
echo 결과: results\numina_balanced_results.json
echo 그라디언트: results\gradient_report_numina*.json
pause
