$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$url = "http://127.0.0.1:8765"
$server = $null

try {
  $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1
  $running = $response.StatusCode -eq 200
} catch {
  $running = $false
}

if (-not $running) {
  $server = Start-Process -FilePath "python" -ArgumentList "dashboard/server.py" -WorkingDirectory $root -PassThru -WindowStyle Hidden
  Start-Sleep -Seconds 1
}

Start-Process $url

Write-Host "Starlight Voice dashboard opened: $url"
if ($server) {
  Write-Host "Server PID: $($server.Id)"
} else {
  Write-Host "Server already running on 127.0.0.1:8765"
}
Write-Host "Ratings file: $root\dashboard\ratings.jsonl"
