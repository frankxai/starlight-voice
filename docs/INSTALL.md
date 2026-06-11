# Install Starlight Voice

This guide is for installing the current repo on a second Windows laptop.

## Reality Check

As of this repo state, Starlight Voice is a buildable Tauri tray scaffold plus specs and plans. It is not yet a complete voice assistant installer.

You can install and verify the tray shell today. The full voice loop is pending the Python sidecar tasks in `docs/PLAN.md`.

## Prerequisites

- Windows 11
- Git
- Rust stable toolchain from `https://rustup.rs`
- PowerShell 7 recommended

Later sidecar work will also require:

- `uv`
- Python 3.12+
- provider keys for Deepgram, Cartesia, Cerebras, Anthropic/OpenAI/Groq as needed

## Clone

```powershell
git clone https://github.com/frankxai/starlight-voice.git C:\Users\frank\starlight-voice
cd C:\Users\frank\starlight-voice
```

Use a different directory if the Windows username is not `frank`.

## Build

```powershell
cargo build --release -p starlight-voice-tauri
```

The built binary should appear at:

```text
target\release\starlight-voice-tauri.exe
```

## Run

```powershell
& .\target\release\starlight-voice-tauri.exe
```

Expected current behavior:

- tray app launches
- no visible terminal window
- no browser window
- no main app window

If a visible console opens, inspect `tauri/src/main.rs` and `tauri/tauri.conf.json` before continuing.

## Environment

The voice sidecar is not implemented yet. When it lands, create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Then fill only the provider keys you actually use. Never commit `.env`.

## Current Verification

```powershell
cargo build --release -p starlight-voice-tauri
```

Manual check:

```powershell
& .\target\release\starlight-voice-tauri.exe
```

Then confirm the process is running:

```powershell
Get-Process | Where-Object { $_.ProcessName -match 'starlight-voice' }
```

## Full Installer Status

The planned one-command installer is not present yet. The intended future flow is documented in `docs/PLAN.md` under the install and legacy-task migration tasks.

Do not remove legacy SIS or Arcanea voice scheduled tasks from a production laptop until those migration scripts exist and have been tested.
