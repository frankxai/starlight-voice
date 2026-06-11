# Starlight Voice

Open-source reference implementation of a Jarvis-grade personal voice operator.

Starlight Voice is the extracted voice runtime for the Starlight ecosystem: a Tauri tray shell plus a planned Python sidecar for push-to-talk capture, low-latency STT/LLM/TTS, and MCP-driven tool access.

## Current State

This repo is **portable but not finished**.

What exists today:

- Rust/Tauri tray application scaffold
- committed `Cargo.lock` for reproducible builds
- first-principles spec at `docs/SPEC.md`
- week 1-3 implementation plan at `docs/PLAN.md`
- handoff and pickup notes in `docs/`

What is still pending:

- Python sidecar scaffold
- push-to-talk hotkey behavior
- STT/LLM/TTS voice loop
- MCP server/client wiring
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

Run the tray scaffold:

```powershell
& .\target\release\starlight-voice-tauri.exe
```

Expected current behavior: a tray-only app starts without opening a terminal, browser, or main window.

## Configuration

Copy `.env.example` to `.env` only when the sidecar work begins:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`.

## Install Guide

See `docs/INSTALL.md` for second-laptop setup and the current limitations.

## Roadmap

The canonical implementation plan is `docs/PLAN.md`.

Milestones:

- Task 1-2: repo + Tauri tray scaffold shipped
- Task 3-9: Python sidecar, CI, tray menu, PTT, autostart, IPC
- Task 10-16: first working voice loop
- Task 17-29: cognition router, MCP, installer, legacy-task migration, benchmark gate

## License

MIT. See `LICENSE`.
