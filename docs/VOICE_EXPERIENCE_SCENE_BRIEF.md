# Starlight Voice Experience — Scene And Runtime Brief

**Date:** 2026-07-18  
**Surface:** Local operator voice experience inside `starlight-voice`  
**Audience:** Frank operating Starlight from desktop, tablet or phone  
**Primary task:** start a voice session, understand exactly what the system is doing and interrupt safely.

## First read

- **What:** a real-time voice command surface for Starlight.
- **For whom:** Frank, as operator.
- **Main object:** the Signal Core — a functional visualization of input level, turn state and transport health.
- **Next action:** press **Start listening**.
- **Trust:** local microphone permission is user-initiated; no external provider is claimed unless one is connected; tool actions remain approval-gated.

## Visual idea

**A quiet observatory around one live signal.**

The Signal Core is not decorative. Its silhouette, energy and color communicate:

| State | Meaning | Visual behavior |
| --- | --- | --- |
| `ready` | no microphone capture | stable dark core with a thin orbital horizon |
| `requesting` | browser permission prompt | restrained inward pulse |
| `listening` | mic capture active | amplitude follows measured RMS/peak energy |
| `transcribing` | committed component-lane audio is resolving to text | discrete boundary frame |
| `thinking` | turn committed, model pending | slow converging bands; no fake random speech |
| `speaking` | assistant audio active | controlled outward cadence |
| `interrupted` | barge-in accepted | fast, clean contraction and state acknowledgement |
| `error` | permission, device or transport failure | quiet red edge and actionable text; never an endless spinner |

## Composition

### Desktop

- 12-column frame, maximum width 1440 px.
- Left 7 columns: state label, concise transcript, Signal Core and primary controls.
- Right 5 columns: live turn trace, audio contract and privacy/session facts.
- At least 45 percent quiet space around the Signal Core.
- No card grid. One primary panel and one evidence rail.

### Mobile

- Signal Core remains above the fold and is smaller, not cropped.
- Primary control is thumb reachable.
- Transcript is two lines before expansion.
- Evidence rail becomes a compact disclosure below the controls.
- Ambient detail is reduced and no essential information depends on motion.

## Typography and material

- Reuse `/tokens.css`; new component values must be mapped through local CSS variables.
- Display: estate serif stack for the operator statement only.
- Interface: estate/system sans stack.
- Metrics/state: estate/system monospace stack.
- Obsidian base, restrained violet signal and warm gold only for confirmed state.
- Glass is limited to one control surface and one evidence rail.

## Interaction contract

### Primary flow

1. User presses **Start listening**.
2. Browser requests microphone permission.
3. On success, the app creates one AudioContext and one analyser graph.
4. Mic RMS and peak energy drive the Signal Core.
5. The user can stop at any time.
6. Spacebar performs push-to-talk only when focus is not on an interactive element.
7. Escape interrupts the active turn and returns to listening or ready safely.
8. A **Run guided turn** control demonstrates deterministic `listening → transcribing → thinking → speaking → listening` behavior without pretending to call a model.

### Honesty rules

- `Local signal` means the mic analyser is running locally.
- `Guided turn` means a deterministic UI demonstration.
- `Realtime connected` may appear only after an actual provider transport reports connected.
- Voice lock is deferred; PTT is the current floor-control mode.
- Browser capture format is measured after permission and displayed separately from the canonical transport contract.
- Never display fabricated latency, transcript or tool results.
- If microphone permission is denied, show recovery steps and keep the experience usable in guided mode.

### Accessibility

- Full keyboard operation.
- Visible focus rings.
- `aria-live` status text for state changes.
- Canvas has a semantic text equivalent.
- Reduced motion disables ambient loops and uses discrete state frames.
- High-contrast control labels and minimum 44 px touch targets.
- No audible autoplay.

## Audio boundary

Canonical analysis and transport preparation:

- sample rate: 48,000 Hz;
- channels: mono;
- internal samples: normalized Float32 in `[-1, 1]`;
- outbound PCM transport helper: signed 16-bit little-endian;
- both production Pipecat lanes construct `LocalAudioTransport` through one builder pinned to 48 kHz mono input/output;
- unsupported devices fail at transport startup instead of silently changing the session contract;
- adapters that do not originate from the pinned local transport must call the non-overridable canonicalizer before their first outbound frame;
- all frames preserve the same contract for the session;
- chunk duration is explicit and testable;
- clipping, malformed channel buffers and invalid sample rates fail loudly.

WebRTC is the Perplexity-proven benchmark transport because it owns media negotiation, Opus alignment and realtime delivery. Starlight ships its already-inspectable Pipecat component lane first and promotes Realtime only after common audio, interruption and latency gates are measured.

## Runtime architecture

```text
User gesture
  → MediaDevices.getUserMedia({ echoCancellation, noiseSuppression, autoGainControl })
  → Web Audio analyser (local-only RMS/peak)
  → VoiceSessionController state machine
  → Signal Core canvas + semantic status + turn trace

Selected MVR voice lane
  → existing Pipecat component pipeline
  → Groq STT → pinned OpenRouter LLM → ElevenLabs TTS
  → local speakers, PTT interruption and measured first-playable audio

Controlled benchmark lane
  → common 48 kHz mono capture contract
  → WebRTC / Opus
  → OpenAI Realtime-1.5
  → promotion only after measured comparison
```

## Technical selection

### Selected now

- HTML/CSS/JavaScript already used by the repo.
- Canvas 2D for the Signal Core.
- Web Audio API for user-initiated microphone analysis.
- No new package, build system or external visual asset.
- Python pure-function audio contract and tests.

### Deferred behind production gates

- OpenAI Realtime session minting and paid model activation.
- Provider credentials.
- External tool execution.
- Public deployment, DNS, SIP and telephony.
- Any proprietary voice imitation.

## Motion score

| Beat | Job | Trigger | Duration | Silent equivalent |
| --- | --- | --- | --- | --- |
| core wake | confirm mic activation | permission granted | 420 ms | state label changes to Listening |
| amplitude response | show real input energy | mic samples | continuous, smoothed | level meter and numeric dB value |
| thought converge | distinguish processing from listening | guided/real turn committed | 900 ms loop | Thinking label and trace entry |
| answer release | distinguish assistant output | playback starts | audio-duration bound | Speaking label and trace entry |
| interruption lock | prove user regained control | Escape/PTT barge-in | 160 ms | Interrupted status and focus return |

No sound cue is added. Microphone capture and eventual assistant playback are inherently audio; additional sonic decoration would reduce clarity.

## Acceptance criteria

- `/voice/` and `/voice/index.html` load from the fail-closed local server.
- Start listening requests microphone permission only after a user action.
- Live level visibly and semantically responds to real microphone input.
- Stop closes all tracks and the AudioContext.
- Guided turn is deterministic and clearly labelled as a demo.
- Escape interruption is immediate.
- State transitions reject invalid sequences.
- 48 kHz mono resampling and PCM16 encoding pass deterministic unit tests.
- Existing server and sidecar tests remain green.
- Desktop and mobile screenshots are inspected.
- Reduced-motion mode remains understandable.
- No new third-party runtime or unproven vendor claim is introduced.
