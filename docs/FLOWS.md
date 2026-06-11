# Flows

These are the flows the product is being built around.

## Flow 1: Quick Voice Ask

1. Hold global PTT.
2. Say a short request.
3. Sidecar routes to fast path.
4. Assistant speaks back briefly.

Target: first audio under 800 ms P50 after mic release.

Current state: text-mode routing exists; microphone and TTS are pending.

## Flow 2: Deep Thinking

1. Hold PTT.
2. Say "think hard about..."
3. Assistant immediately says a short acknowledgement.
4. Deliberation lane runs in the background.
5. Assistant returns a concise spoken summary.
6. Full transcript/receipt is available in logs.

Current state: deliberation classification exists; live Claude/Codex execution is pending.

## Flow 3: Browser Action

1. Ask for an explicit browser task.
2. Router selects `tier3-browser`.
3. Browser adapter starts in dry-run or confirmation mode.
4. Live browser-use execution produces a screenshot/action receipt.
5. Destructive actions pause for approval.

Current state: browser dry-run exists; live sandbox and receipts are pending.

## Flow 4: Coding Agent Handoff

1. Ask for a code task.
2. Router detects Codex/Claude/OpenCode/Gemini lane.
3. `arco` picks the right installed CLI.
4. The selected CLI receives a scoped task and returns a receipt.

Current state: `arco doctor` works; sidecar has CLI-agent classification. Execution pool is pending.

## Flow 5: Morning Machine Check

1. Run `pwsh -File scripts/doctor.ps1`.
2. Check toolchain, agent CLIs, optional packages, and readiness.
3. Run `pwsh -File scripts/test-local.ps1` before committing runtime changes.

Current state: working.

## Flow 6: Installed Daily Driver

1. Windows logon starts one hidden scheduled task.
2. Tauri tray appears.
3. Sidecar starts hidden.
4. Health check passes.
5. PTT is ready.

Current state: not shipped. This is the core remaining engineering slice.
