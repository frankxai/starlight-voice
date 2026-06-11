$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$url = "http://127.0.0.1:8765"
$server = Start-Process -FilePath "python" -ArgumentList "dashboard/server.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 1
Start-Process $url

Write-Host "Starlight Voice dashboard opened: $url"
Write-Host "Server PID: $($server.Id)"
Write-Host "Ratings file: $root\dashboard\ratings.jsonl"
