# Perplexity Voice Implementation — Evidence Brief

**As-of:** 2026-07-18  
**Target:** Starlight Voice  
**Confidence rule:** direct product evidence is separated from inference. Visual resemblance, package presence and public repositories are not treated as proof.

## Multi-agent decision

Build the Starlight experience around Perplexity's proven interaction and audio lessons, but ship the repository's already-inspectable **Component A** lane first:

```text
Groq streaming STT
  → OpenRouter fast LLM with provider pin
  → ElevenLabs streaming TTS
  → Pipecat local audio transport
```

Keep **OpenAI Realtime-1.5 over WebRTC** as the evidence-backed benchmark lane. Promote it only if it wins the same measured capture, first-playable-audio, interruption, intelligibility and tool-safety gates.

For the interaction surface, use dependency-free **HTML/CSS/Canvas/Web Audio**, matching the existing dashboard and planned Tauri WebView shell. React, React Three Fiber and GSAP add build/runtime cost without improving this single stateful signal object.

## Verified Perplexity implementation facts

The strongest implementation source is OpenAI's engineering article, co-authored by **Paul Fryzel of Perplexity** and **Charu Jaiswal of OpenAI**, published 2026-03-25.

The article states that Perplexity:

- uses **Realtime-1.5 in production** for millions of voice sessions each month across Computer and Comet;
- changed large context updates to incremental chunks of about **2,000 tokens** so truncation fails gracefully;
- preserves semantic roles: `system` for policy, `user` for actual user speech and `assistant` for generated output;
- learned not to present background webpage/context material as if the user had spoken it;
- built a shared **Rust audio SDK** across Swift, TypeScript, Rust and C++ clients;
- standardizes audio before it reaches the server at **48 kHz mono**;
- aligns the waveform with **Opus** and WebRTC's internal rate;
- runs audio through **WebRTC APM** for echo cancellation, automatic gain control, noise reduction and high-pass filtering before transport encoding;
- tunes VAD against actual microphones, speaker volume and noisy real-world conditions, including an internal noisy-bar test;
- uses ambient voice by default and introduced **voice lock** so the user can retain the floor through pauses;
- narrows tool exposure to **under ten core tools**;
- gives explicit tool instructions and returns ordinary structured tool JSON, separating user-facing `response_text` from control flags such as `require_repeat_verbatim`.

These are direct implementation facts. The article does not identify Perplexity's visual orb renderer.

## Confirmed application estate

Perplexity's active engineering listings say its Perplexity, Computer, Comet and native application teams work across:

- Chromium;
- Rust;
- Kotlin;
- Swift;
- TypeScript;
- Perplexity's core AI stack.

This confirms a multi-runtime application estate. It does not disclose which renderer draws the voice visualization on each surface.

## Named vendor evidence

| Vendor | What the source supports | What it does not support |
| --- | --- | --- |
| OpenAI | Perplexity uses Realtime-1.5 in production for Computer/Comet voice at millions of monthly sessions. | It does not identify the visual renderer. |
| ElevenLabs | Perplexity and ElevenLabs partnered on Discover Daily in 2024. | It does not prove that current Computer Voice uses ElevenLabs TTS. |
| LiveKit | Perplexity publishes a LiveKit integration for developers using Perplexity APIs. | It does not prove that Perplexity's shipped Computer voice path uses LiveKit. |

No credible public source was found for Perplexity Computer Voice using ElevenLabs Orb, VoiceOrbs, React Bits Orb, React Three Fiber, Three.js, Lottie, Cartesia, Deepgram or Pipecat. Those remain unverified.

## Starlight translation

### Adopt now

- One canonical **48 kHz mono** audio boundary, enforced by the shared production Pipecat local-transport builder.
- Float32 internal analysis and an explicit PCM16 helper for transports that require it; the canonicalizer cannot accept a runtime target override.
- PTT as the first controlled activation mode because the current Starlight desktop specification is PTT-first.
- Real microphone energy driving one functional Signal Core.
- Honest `ready → requesting → listening → transcribing/thinking → speaking → interrupted/error` states.
- Strict conversation-role separation: system is policy, user is actual speech, assistant is generated output.
- Retrieved memory remains explicitly untrusted frame metadata until a typed tool/reference adapter can admit it; it is never injected into the system-policy role.
- A deliberately small, typed, approval-gated future tool surface.
- Environment tests across microphones, speakers, noise and network conditions.

### Benchmark, do not assume

- Realtime-1.5/WebRTC as the default runtime.
- Ambient voice and Perplexity-style voice lock.
- Any specific model/provider superiority without measured receipts.

### Do not copy

- Perplexity's visual design, animation, product copy or proprietary voices.
- A decorative orb without operational meaning.
- Any vendor claim not supported by a first-party source.

## Sources

1. OpenAI Developers, **How Perplexity Brought Voice Search to Millions Using the Realtime API**, 2026-03-25: <https://developers.openai.com/blog/realtime-perplexity-computer>
2. Perplexity Ashby, **Member of Technical Staff (Software Engineer, Desktop Apps)**: <https://jobs.ashbyhq.com/perplexity/b00cbb00-f672-4909-a7be-bbd02c7d7b5f>
3. Perplexity Ashby, **Member of Technical Staff (Software Engineer, Comet and Native Apps)**: <https://jobs.ashbyhq.com/perplexity/be0bab19-d24e-4233-ab9e-edb6f6a16620>
4. Aravind Srinivas, Computer Voice Control launch post, 2026-03-06: <https://x.com/AravSrinivas/status/2030046292572094918>
5. ElevenLabs, Perplexity partnership announcement, 2024-02-23: <https://elevenlabs.io/blog/elevenlabs-and-perplexity-announce-partnership-2>
6. Perplexity developer docs, LiveKit integration: <https://docs.perplexity.ai/docs/getting-started/integrations/livekit>

## Evidence caveats

- The visual renderer remains closed source and undisclosed.
- CEO launch posts establish product direction, not renderer or transport details.
- The OpenAI article is the controlling source for current Realtime, context, audio, VAD, voice-lock and tool claims.
- Provider and model names must be revalidated before production activation.
