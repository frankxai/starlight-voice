# Usage

Starlight Voice is currently a buildable shell plus a working text/IPC sidecar. Use it in three modes.

## 1. Check This Machine

```powershell
pwsh -File scripts/doctor.ps1
```

This reports:

- local build tools
- agent CLIs
- optional voice/browser packages
- which lanes are ready

Current expected state on Frank's laptop:

- ready: Python, uv, Rust/Cargo, Node/npm, PowerShell, Claude Code, Codex, OpenCode, `arco`
- missing: Gemini CLI
- optional packages present: browser-use, Anthropic SDK, OpenAI SDK, sounddevice
- missing voice-pipeline package: Pipecat

## 2. Run the Sidecar Smoke

```powershell
pwsh -File scripts/smoke-sidecar.ps1
```

This proves:

- sidecar health works
- default fast text path works
- deliberation routing works
- browser dry-run routing works

## 3. Run Full Local Verification

```powershell
pwsh -File scripts/test-local.ps1
```

This runs:

- Python sidecar tests
- router benchmark
- browser dry-run benchmark
- Rust/Tauri release build

## Direct CLI

```powershell
$env:PYTHONPATH = "sidecar/src"
python -m starlight_voice health
python -m starlight_voice doctor
python -m starlight_voice say "open browser and search the docs"
python -m starlight_voice browser "open browser-use docs"
```

## What You Can Use Today

You can use the repo today as:

- a tray-shell build
- a text-mode command router
- a browser-task dry-run router
- a machine-readiness audit
- a foundation for connecting Codex/Claude/OpenCode/Gemini lanes

You cannot yet use it as:

- a live microphone voice loop
- a live browser controller
- a one-click installed background assistant

Those are the next implementation slices.
