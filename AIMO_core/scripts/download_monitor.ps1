$pid = 27800
$dir = 'C:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct'
$log = 'C:\startingup\AIMO\AIMO_core\scripts\download_progress.log'
$maxHours = 48
$endTime = (Get-Date).AddHours($maxHours)

function Write-Log($msg) {
    $line = "$(Get-Date -Format o) - $msg"
    Add-Content -Path $log -Value $line
}

Write-Log "Monitor started for PID $pid, watching $dir"
while ((Get-Date) -lt $endTime) {
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($proc) {
        $procDesc = "PID $($proc.Id) Running CPU=$([math]::Round($proc.CPU,2)) WS(MB)=$([math]::Round($proc.WorkingSet/1MB,1))"
    } else {
        $procDesc = "PID $pid not running"
    }

    if (Test-Path $dir) {
        $files = Get-ChildItem -LiteralPath $dir -File -Recurse -ErrorAction SilentlyContinue
        $safet = $files | Where-Object { $_.Name -match '\.safetensors$' }
        $count = $safet.Count
        $totalBytes = ($files | Measure-Object Length -Sum).Sum
        $totalGB = if ($totalBytes) { [math]::Round($totalBytes/1GB,3) } else { 0 }
        Write-Log "$procDesc | Files=$($files.Count) Safetensors=$count TotalSizeGB=$totalGB"
        $top = $safet | Sort-Object Length -Descending | Select-Object -First 5 | ForEach-Object { "$(($_.Name) -replace 'C:\\startingup\\AIMO\\','') : $([math]::Round($_.Length/1MB,2)) MB" }
        foreach ($t in $top) { Write-Log "  $t" }
    } else {
        Write-Log "$procDesc | Model dir not found"
    }

    # finish condition: all shards present (>=37) and process not running
    if (Test-Path $dir) {
        $safetCount = (Get-ChildItem -LiteralPath $dir -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '\.safetensors$' }).Count
        if ($safetCount -ge 37 -and -not (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            Write-Log "Download complete (safetensors count=$safetCount) and process exited. Exiting monitor."
            break
        }
    }

    Start-Sleep -Seconds 120
}
Write-Log "Monitor finished or timed out."
