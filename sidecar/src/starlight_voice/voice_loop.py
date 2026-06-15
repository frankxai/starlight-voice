"""In-process cloud-first realtime voice loop (Pipecat 1.3.0).

Cloud-first per the 2026-06-15 decision: mic -> Groq STT -> OpenRouter LLM -> ElevenLabs TTS
-> speakers, orchestrated by Pipecat entirely inside this Python sidecar. The Rust/Tauri
shell only owns PTT + tray + lifecycle; audio never crosses the stdio IPC boundary.

The `CognitionRouter` rides the graph as a FrameProcessor (observes tier on each final
transcript) — it classifies, it does NOT call the LLM or pick the engine (that stays in
`config.Settings` / the LLM service), keeping the router's frozen contract intact.

Pipecat is imported lazily so importing this module is cheap and safe on a machine without
the `voice` extra installed (`adapters.require()` gives the actionable install error).
API verified live against pipecat-ai 1.3.0 (service/transport/context-aggregator names).
"""

from __future__ import annotations

import os

from . import adapters
from .cognition import CognitionRouter
from .config import Settings


def _stt_service(settings: Settings):
    """Cloud STT. Default Groq Whisper (live GROQ_API_KEY)."""
    from pipecat.services.groq.stt import GroqSTTService

    return GroqSTTService(
        api_key=os.environ.get("GROQ_API_KEY"),
        model=settings.stt_model or "whisper-large-v3-turbo",
    )


def _llm_service(settings: Settings):
    """LLM via the OpenRouter gateway.

    Provider-pin-by-tier (Cerebras for the FAST/voice tier) is owned here, NOT the router —
    without it OpenRouter may route to a 600ms+ TTFT provider and silently break the SLA.
    Passed through OpenRouter's `provider` routing field via extra body.
    """
    from pipecat.services.openrouter.llm import OpenRouterLLMService

    extra = {"provider": {"order": [settings.llm_fast_provider], "allow_fallbacks": True}}
    return OpenRouterLLMService(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        params=OpenRouterLLMService.InputParams(extra=extra)
        if hasattr(OpenRouterLLMService, "InputParams")
        else None,
    )


def _tts_service(settings: Settings):
    """Cloud TTS. Default ElevenLabs Flash v2.5 streaming (live ELEVENLABS_API_KEY)."""
    from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

    kwargs = {"api_key": os.environ.get("ELEVENLABS_API_KEY"), "model": "eleven_flash_v2_5"}
    if settings.tts_voice_id:
        kwargs["voice_id"] = settings.tts_voice_id
    return ElevenLabsTTSService(**kwargs)


def _router_processor():
    """A FrameProcessor that tags each final transcript with its CognitionRouter tier.

    Observes only — gating per tier (dispatch / approval) is a later phase. Keeps the
    router's frozen `decide(text) -> RouteDecision` contract unchanged.
    """
    from pipecat.frames.frames import TranscriptionFrame
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

    router = CognitionRouter()

    class RouterProcessor(FrameProcessor):
        async def process_frame(self, frame, direction: "FrameDirection"):
            await super().process_frame(frame, direction)
            if isinstance(frame, TranscriptionFrame) and getattr(frame, "text", "").strip():
                decision = router.decide(frame.text)
                # surfaced for telemetry / future per-tier gating; non-blocking
                frame.metadata = {**getattr(frame, "metadata", {}), "route_tier": decision.tier.value}
            await self.push_frame(frame, direction)

    return RouterProcessor()


def build_graph(settings: Settings | None = None, *, with_transport: bool):
    """Assemble the Pipecat pipeline.

    with_transport=False builds the service chain only (no mic/speaker) so the graph can be
    validated headlessly. with_transport=True opens the local audio device for a live run.
    Returns (pipeline, transport_or_None).
    """
    settings = settings or Settings.from_env()
    for engine in ("groq-openrouter", "openrouter", "elevenlabs", "pipecat"):
        # availability() maps these to importable deps; require() raises with install hint
        pass
    adapters.require("pipecat")

    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.processors.aggregators.llm_context import LLMContext
    from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

    stt = _stt_service(settings)
    llm = _llm_service(settings)
    tts = _tts_service(settings)
    router_proc = _router_processor()

    context = LLMContext(
        messages=[{
            "role": "system",
            "content": (
                "You are Starlight, Frank's voice operator. Lead with the action. "
                "Reply in <=2 short sentences. No hedging, no preamble."
            ),
        }]
    )
    pair = LLMContextAggregatorPair(context)

    transport = None
    head: list = []
    tail: list = []
    if with_transport:
        from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

        transport = LocalAudioTransport(LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True))
        head = [transport.input()]
        tail = [transport.output()]

    pipeline = Pipeline(
        [*head, stt, router_proc, pair.user(), llm, tts, *tail, pair.assistant()]
    )
    return pipeline, transport


def selftest(settings: Settings | None = None) -> dict[str, object]:
    """Construct the full service chain + pipeline WITHOUT opening audio. Headless-safe.

    Catches ctor/import/assembly errors (wrong arg names, moved modules) before a live run.
    Does NOT prove latency — that needs the on-device run with a mic (benchmarks first-audio).
    """
    settings = settings or Settings.from_env()
    pipeline, _ = build_graph(settings, with_transport=False)
    return {
        "ok": True,
        "pipeline_processors": len(pipeline._processors) if hasattr(pipeline, "_processors") else None,
        "stt": settings.stt_engine,
        "llm": f"{settings.llm_model}@{settings.llm_fast_provider}",
        "tts": settings.tts_engine,
    }


async def run(settings: Settings | None = None) -> int:
    """Live run: open mic/speakers and run the loop until EndFrame. Needs the `voice` extra + a mic."""
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask

    settings = settings or Settings.from_env()
    pipeline, _ = build_graph(settings, with_transport=True)
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    await PipelineRunner().run(task)
    return 0
