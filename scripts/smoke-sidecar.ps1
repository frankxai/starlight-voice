$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONPATH = "sidecar/src"

Write-Host "== Health =="
python -m starlight_voice health

Write-Host ""
Write-Host "== Fast path =="
python -m starlight_voice say "hello"

Write-Host ""
Write-Host "== Deliberation path =="
python -m starlight_voice say "think hard about the architecture tradeoff"

Write-Host ""
Write-Host "== Browser dry-run =="
python -m starlight_voice browser "open browser-use docs"
