"""Coding-agent fleet routing — which CLI handles a dispatched task.

Mirror of SIS `agents/CODING_AGENTS_REGISTRY.md` (complexity-band routing + the cl/cd/agy
command grid), with the corrected June-2026 model IDs. The voice operator classifies a task's
complexity, picks the cheapest agent that can handle it, and (via dispatch.py) emits a
handoff-packet and spawns the CLI.

Routing doctrine (registry §2):
  1-3 trivial   -> OpenCode / Codex     (speed, minimal cost)
  4-6 medium    -> Cursor / Cline       (interactive)
  7-8 high      -> Claude Code / agy     (autonomous, deep context)  -- default coding seat: Fable 5
  9-10 substrate-> DeepAgent / Hive      (sub-agent delegation)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FleetAgent:
    name: str            # human/registry name
    cli: str             # current-directory command-grid alias (registry §3)
    model: str           # corrected June-2026 model id (OpenRouter strings where applicable)
    min_complexity: int
    max_complexity: int

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "cli": self.cli, "model": self.model}


# Ordered by complexity band. Gemini CLI intentionally ABSENT — it shuts down 2026-06-18;
# the Gemini-family seat is Antigravity (`agy`). Fable 5 leads Terminal-Bench 2.1 (88%) so it
# holds the 7-8 coding seat; Opus 4.8 is the deep-reasoning alternate (same `cl` CLI).
FLEET: tuple[FleetAgent, ...] = (
    FleetAgent("OpenCode", "opencode", "groq/llama-4-scout", 1, 3),
    FleetAgent("Codex CLI", "cd", "openai/gpt-5", 1, 3),
    FleetAgent("Cursor", "cursor", "anthropic/claude-opus-4-8", 4, 6),
    FleetAgent("Claude Code", "cl", "claude-fable-5", 7, 8),
    FleetAgent("Antigravity", "agy", "gemini-3-pro", 7, 8),
    FleetAgent("DeepAgent", "dcode", "claude-opus-4-8", 9, 10),
)

# Keyword signals for a coarse 1-10 complexity estimate. Deliberately simple + auditable;
# the router already gated this as a CLI_AGENT task, so we only size it here.
_HIGH = ("refactor", "migrate", "architecture", "test suite", "fix build", "multi-file", "across the repo", "debug")
_SUBSTRATE = ("substrate", "sip", "protocol", "schema migration", "breaking change", "whole codebase")
_TRIVIAL = ("rename", "typo", "bump", "update readme", "add comment", "format", "one-liner", "small script")


def complexity_score(task: str) -> int:
    """Coarse 1-10 sizing of a coding task from keyword signals + length."""
    t = " ".join(task.lower().split())
    if any(k in t for k in _SUBSTRATE):
        return 9
    if any(k in t for k in _HIGH):
        return 7
    if any(k in t for k in _TRIVIAL):
        return 2
    # default: medium, nudged up for long/compound asks
    return 5 if len(t) < 160 and " and " not in t else 6


def select_agent(score: int) -> FleetAgent:
    """Cheapest agent whose band covers the score; clamps to [1,10]."""
    score = max(1, min(10, score))
    for agent in FLEET:
        if agent.min_complexity <= score <= agent.max_complexity:
            return agent
    return FLEET[-1]  # 9-10 fallthrough
