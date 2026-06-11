# Starlight Voice Architecture

This is the implementation-facing architecture for the repo. `docs/SPEC.md` is the origin story; this file is the daily build contract.

## Design Posture

Starlight Voice is a local-first voice operator, not a SaaS voice bot.

The best current systems split concerns cleanly:

- Tauri owns operating-system integration: tray, hotkey, autostart, sidecar lifecycle.
- Python owns the agent runtime: voice pipeline, model adapters, browser automation, MCP tools.
- Browser work is a capability lane, not a hidden always-on browser at boot.
- Public docs must state what is real today and what is planned.

## Current Primary References

- Pipecat: open-source Python framework for realtime voice and multimodal agents, with service/transports/pipeline composition. <https://docs.pipecat.ai/overview/introduction>
- LiveKit Agents: production-ready voice AI agent framework and WebRTC deployment path. <https://docs.livekit.io/agents/>
- OpenAI Voice Agents / Realtime: useful browser/mobile WebRTC option and reference for session lifecycle. <https://developers.openai.com/api/docs/guides/voice-agents>
- browser-use: browser automation agent stack with Python API and native core runtime. <https://github.com/browser-use/browser-use>

## Architecture Decision

Default desktop path:

```text
Tauri tray + PTT hotkey
  -> Python sidecar JSON-lines IPC
  -> Pipecat pipeline
  -> STT / LLM / TTS providers
  -> speakers
```

Browser/mobile path:

```text
Phone or browser client
  -> WebRTC / Realtime transport
  -> sidecar or hosted relay
  -> same cognition/tool layer
```

Browser automation path:

```text
voice/text request
  -> CognitionRouter tier3-browser
  -> BrowserAutomationAdapter
  -> browser-use or hosted browser provider
```

## What Exists Now

- Tauri tray shell builds.
- Python sidecar package exists.
- JSON-lines IPC handles `health`, `utterance`, and `browser.task`.
- Browser-use adapter supports dry-run routing and explicit live gating.
- Router classifies control, fast chat, deliberation, CLI-agent, and browser tasks.
- CI builds Rust and tests Python.
- Benchmarks smoke the low-latency routing path.

## What Must Exist Before Calling It Daily-Driver

- Global PTT hotkey wired to sidecar.
- Microphone capture and audio output.
- Pipecat voice pipeline with real STT/LLM/TTS adapters.
- MCP client with a constrained tool registry.
- Browser live execution sandbox policy.
- Installer with one hidden scheduled task.
- Legacy scheduled-task migration scripts.
- Latency gate for hot-path P50.

## Performance Targets

See `benchmarks/budgets.toml`.

Non-negotiables:

- zero visible windows at logon
- one scheduled task owned by Starlight Voice
- router decision P50 under 10 ms
- dry-run browser routing P50 under 50 ms
- mic close to first audio P50 under 800 ms when provider path is live

## Interface Standard

The voice interface should feel calm, premium, and precise:

- no fake certainty
- short spoken responses by default
- immediate acknowledgement before long reasoning
- visible tray state: idle, listening, thinking, error
- no browser or dashboard unless explicitly requested
