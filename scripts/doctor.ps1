$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONPATH = "sidecar/src"
python -m starlight_voice doctor

Write-Host ""
Write-Host "Agent router:"
arco doctor
