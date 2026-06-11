from __future__ import annotations

from time import perf_counter

from . import __version__
from .cognition import CognitionRouter, RouteTier


class AgentPipeline:
    """Text-first skeleton for the future Pipecat audio graph.

    Voice is an audio transport problem plus a reasoning/tool problem. This class
    gives the reasoning/tool side a stable contract before microphone, STT, and
    TTS adapters are wired.
    """

    def __init__(self) -> None:
        self.router = CognitionRouter()

    def health(self) -> dict[str, object]:
        return {
            "service": "starlight-voice-sidecar",
            "version": __version__,
            "status": "ok",
            "capabilities": {
                "text_mode": True,
                "voice_loop": False,
                "browser_dry_run": True,
                "browser_live": False,
                "doctor": True,
                "mcp": False,
            },
        }

    def process_text(self, text: str) -> dict[str, object]:
        started = perf_counter()
        decision = self.router.decide(text)
        response = self._response_for(decision.tier, text)
        return {
            "input": text,
            "route": decision.to_dict(),
            "response": response,
            "elapsed_ms": int((perf_counter() - started) * 1000),
        }

    @staticmethod
    def _response_for(tier: RouteTier, text: str) -> dict[str, object]:
        if tier == RouteTier.CONTROL:
            return {"type": "control", "text": f"Control command acknowledged: {text}"}
        if tier == RouteTier.BROWSER:
            return {"type": "browser", "text": "Browser task routed. Use browser.task IPC to execute or dry-run."}
        if tier == RouteTier.CLI_AGENT:
            return {"type": "handoff", "text": "CLI-agent task routed. Codex/Claude/OpenCode pool wiring is next."}
        if tier == RouteTier.DELIBERATION:
            return {"type": "deliberation", "text": "I will take the slower reasoning lane for this."}
        return {"type": "voice", "text": "Starlight Voice text path is alive."}
