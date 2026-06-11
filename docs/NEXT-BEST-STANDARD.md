# Next Best Standard

This is the bar Starlight Voice is aiming at.

## Product Standard

The interface should feel like a quiet executive operator:

- beautiful voice, short replies, no rambling
- push-to-talk first, ambient modes opt-in only
- tray-native presence, no boot chaos
- browser automation available on command, never hidden
- fast-path response first, deep reasoning only when requested or clearly needed

## Engineering Standard

Every major feature needs:

- a current-state doc update
- tests or benchmark smoke
- explicit degraded mode
- no secrets in Git
- no new always-on process without an owner and uninstall path

## Technical Direction

1. Keep Pipecat as the default Python voice pipeline.
2. Keep LiveKit/WebRTC as the future remote/mobile transport.
3. Keep OpenAI Realtime as an optional browser/mobile provider lane, not the whole architecture.
4. Keep browser-use as the first local browser automation adapter.
5. Add hosted browser providers only behind policy, logs, and user confirmation.
6. Use MCP for cross-repo tools and substrate access.
7. Keep Codex/Claude/OpenCode/Gemini as explicit CLI-agent lanes.

## Next Implementation Slice

1. Rust sidecar process manager.
2. JSON-lines IPC smoke from Rust to Python.
3. Tray menu: Pause, Health, Quit.
4. PTT hotkey events over IPC.
5. Pipecat local text-to-audio harness.
6. Browser-use live sandbox with screenshot receipt.
