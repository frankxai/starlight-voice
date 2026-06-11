$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== Python sidecar tests =="
$env:PYTHONPATH = "sidecar/src"
python -m pytest sidecar/tests

Write-Host ""
Write-Host "== Router benchmark =="
python benchmarks/run.py --probe router --n 25

Write-Host ""
Write-Host "== Browser dry-run benchmark =="
python benchmarks/run.py --probe browser-dry-run --n 25

Write-Host ""
Write-Host "== Rust/Tauri release build =="
cargo build --release -p starlight-voice-tauri
