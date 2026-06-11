from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter


class RouteTier(StrEnum):
    CONTROL = "tier0-control"
    FAST = "tier1-fast"
    DELIBERATION = "tier25-deliberation"
    BROWSER = "tier3-browser"
    CLI_AGENT = "tier3-cli-agent"


@dataclass(frozen=True)
class RouteDecision:
    tier: RouteTier
    intent: str
    reason: str
    elapsed_ms: int

    def to_dict(self) -> dict[str, object]:
        return {
            "tier": self.tier.value,
            "intent": self.intent,
            "reason": self.reason,
            "elapsed_ms": self.elapsed_ms,
        }


class CognitionRouter:
    CONTROL_WORDS = {
        "pause",
        "resume",
        "stop listening",
        "quit",
        "status",
        "health",
    }

    BROWSER_HINTS = {
        "browser",
        "browse",
        "open website",
        "go to",
        "search the web",
        "click",
        "fill form",
        "screenshot",
    }

    CLI_HINTS = {
        "codex",
        "claude code",
        "opencode",
        "gemini",
        "refactor repo",
        "run tests",
        "fix build",
    }

    DELIBERATION_HINTS = {
        "think hard",
        "starlight-board",
        "sip",
        "substrate",
        "architecture",
        "governance",
        "tradeoff",
    }

    def decide(self, text: str) -> RouteDecision:
        started = perf_counter()
        normalized = " ".join(text.lower().split())

        if normalized in self.CONTROL_WORDS:
            return self._decision(RouteTier.CONTROL, "control", "Exact control phrase.", started)

        if self._contains_any(normalized, self.BROWSER_HINTS):
            return self._decision(RouteTier.BROWSER, "browser-task", "Browser automation hint detected.", started)

        if self._contains_any(normalized, self.CLI_HINTS):
            return self._decision(RouteTier.CLI_AGENT, "cli-agent-task", "CLI agent hint detected.", started)

        if self._contains_any(normalized, self.DELIBERATION_HINTS):
            return self._decision(RouteTier.DELIBERATION, "deliberation", "Deep reasoning hint detected.", started)

        return self._decision(RouteTier.FAST, "fast-chat", "Default low-latency path.", started)

    @staticmethod
    def _contains_any(text: str, needles: set[str]) -> bool:
        return any(needle in text for needle in needles)

    @staticmethod
    def _decision(tier: RouteTier, intent: str, reason: str, started: float) -> RouteDecision:
        return RouteDecision(tier=tier, intent=intent, reason=reason, elapsed_ms=int((perf_counter() - started) * 1000))
