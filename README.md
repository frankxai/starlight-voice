# Starlight Voice

Open-source reference implementation of a Jarvis-grade personal voice operator.

Starlight Voice is the extracted voice runtime for the Starlight ecosystem: a Tauri tray shell plus a planned Python sidecar for push-to-talk capture, low-latency STT/LLM/TTS, and MCP-driven tool access.

## Current State

This repo is **portable but not finished**.

What exists today:

- Rust/Tauri tray application scaffold
- Python sidecar scaffold with text-mode CLI
- JSON-lines IPC for `health`, `utterance`, and `browser.task`
- machine doctor for installed tools and readiness
- cognition router for fast, deliberation, browser, CLI-agent, and control paths
- browser automation adapter seam with safe dry-run mode
- benchmark smoke scripts and GitHub Actions CI
- committed `Cargo.lock` for reproducible builds
- first-principles spec at `docs/SPEC.md`
- implementation architecture at `docs/ARCHITECTURE.md`
- week 1-3 implementation plan at `docs/PLAN.md`
- handoff and pickup notes in `docs/`

What is still pending:

- push-to-talk hotkey behavior
- STT/LLM/TTS voice loop
- MCP server/client wiring
- live browser automation sandbox
- signed installer
- legacy SIS/Arcanea task migration scripts

## Quick Start

Prerequisites:

- Windows 11
- Git
- Rust stable toolchain

Clone and build:

```powershell
git clone https://github.com/frankxai/starlight-voice.git C:\Users\frank\starlight-voice
cd C:\Users\frank\starlight-voice
cargo build --release -p starlight-voice-tauri
```

Run sidecar tests:

```powershell
python -m pip install pytest
$env:PYTHONPATH = "sidecar/src"
python -m pytest sidecar/tests
```

Inspect this machine:

```powershell
pwsh -File scripts/doctor.ps1
```

Run the tray scaffold:

```powershell
& .\target\release\starlight-voice-tauri.exe
```

Expected current behavior: a tray-only app starts without opening a terminal, browser, or main window.

Run the text-mode sidecar:

```powershell
$env:PYTHONPATH = "sidecar/src"
python -m starlight_voice health
python -m starlight_voice doctor
python -m starlight_voice say "open browser and search the docs"
python -m starlight_voice browser "open the Pipecat docs"
```

## Configuration

Copy `.env.example` to `.env` only when the sidecar work begins:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`.

## Install Guide

See `docs/INSTALL.md` for second-laptop setup and the current limitations.

Useful docs:

- `docs/USAGE.md` — how to run and test it
- `docs/CAPABILITIES.md` — what is real now versus planned
- `docs/FLOWS.md` — the target Jarvis-grade flows
- `docs/ARCHITECTURE.md` — engineering architecture

## Roadmap

The canonical implementation plan is `docs/PLAN.md`.

Milestones:

- Task 1-2: repo + Tauri tray scaffold shipped
- Task 3 partial: Python sidecar + IPC contract shipped
- Task 4 partial: CI + benchmark smoke shipped
- Current: machine doctor, capability docs, and usage scripts shipped
- Next: Rust sidecar process manager, tray menu, PTT, autostart IPC
- Task 10-16: first working voice loop
- Task 17-29: cognition router, MCP, installer, legacy-task migration, benchmark gate

## License

MIT. See `LICENSE`.
