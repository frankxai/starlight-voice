# Provider Options

Starlight Voice should not bet the whole product on one provider. The best architecture is a local shell and sidecar with provider lanes.

## Recommended Shape

Use the **Hybrid Starlight** path:

- Tauri owns the local daily-driver surface.
- Pipecat owns the voice pipeline.
- OpenAI Realtime is a browser/mobile lane.
- ElevenLabs is an expressive voice / agent lane.
- browser-use is the browser automation lane.
- Codex, Claude Code, OpenCode, and Gemini are coding-agent lanes through `arco`.

## Option A: ElevenLabs Agent

Use when the highest priority is beautiful, expressive voice and a fast polished conversation surface.

Good for:

- warm assistant personality
- high-quality speech feel
- fast prototype of a voice-first UI

Watch-outs:

- keep external tools and browser execution behind a server-side policy layer
- avoid making ElevenLabs the only orchestration brain

References:

- ElevenAgents overview: <https://elevenlabs.io/docs/eleven-agents/overview>
- ElevenLabs React/WebRTC library: <https://elevenlabs.io/docs/eleven-agents/libraries/react>
- ElevenLabs WebSocket docs: <https://elevenlabs.io/docs/eleven-agents/libraries/web-sockets>

## Option B: OpenAI Realtime

Use when speech-to-speech, tool calling, and agent workflow should share the OpenAI stack.

Good for:

- browser/mobile WebRTC voice
- unified realtime model + tool workflow
- strong server-side control patterns

Watch-outs:

- keep business logic and private tools server-side
- prefer WebRTC for browser/mobile clients and WebSocket for server-to-server paths

References:

- OpenAI Voice Agents: <https://developers.openai.com/api/docs/guides/voice-agents>
- OpenAI Realtime WebRTC: <https://developers.openai.com/api/docs/guides/realtime-webrtc>
- OpenAI Realtime WebSocket: <https://developers.openai.com/api/docs/guides/realtime-websocket>
- Server-side controls: <https://developers.openai.com/api/docs/guides/realtime-server-controls>

## Option C: OSS Experiment Stack

Use when sovereignty, inspectability, and composability matter most.

Good for:

- local iteration
- durable architecture
- custom provider routing
- browser automation through open tooling

Watch-outs:

- more engineering burden
- voice beauty depends on selected provider lanes

References:

- Pipecat: <https://docs.pipecat.ai/overview/introduction>
- Pipecat Flows: <https://docs.pipecat.ai/pipecat-flows/introduction>
- browser-use: <https://github.com/browser-use/browser-use>
- browser-use docs: <https://docs.browser-use.com/cloud/quickstart>

## Option D: Hybrid Starlight

This is the recommended architecture.

Use provider lanes as replaceable capabilities:

- ElevenLabs for beauty
- OpenAI Realtime for unified realtime agent experiences
- Pipecat for provider-neutral voice pipeline control
- browser-use for browser execution
- Codex/Claude/OpenCode/Gemini for coding execution

The dashboard at `dashboard/index.html` lets Frank rate these paths. Run it with:

```powershell
pwsh -File scripts/open-dashboard.ps1
```
