"""Dispatch a coding task to the fleet via the agent-handoff-packet contract.

Flow: task -> complexity_score -> select_agent -> build handoff-packet -> approval gate
-> (Tier A) fire-and-forget pwsh spawn of the chosen CLI, or surface for ack (Tier B/C).

Safety mirrors browser.py: `live=False` by default — dispatch builds and returns the packet
without spawning, so the voice path can preview "Routing to Fable 5, diff ready for review"
before anything executes. Spawns use ABSOLUTE paths (subagent ~ -path footgun) and never block.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone

import ulid

from .fleet import FleetAgent, complexity_score, select_agent

# Tier doctrine (PRD §4 approval gates):
#   A free  — read/search/scoped edits run immediately
#   B ack   — destructive / publish / merge / spend -> require Frank ack
#   C stop  — substrate / irreversible -> escalate to board
_TIER_B = ("delete", "remove", "force push", "force-push", "publish", "deploy", "merge", "drop table", "rm -rf", "reset --hard", "send email", "charge")
_TIER_C = ("substrate", "sip", "protocol", "sovereignty", "rotate", "migration")


def approval_tier(task: str) -> str:
    t = " ".join(task.lower().split())
    if any(k in t for k in _TIER_C):
        return "C"
    if any(k in t for k in _TIER_B):
        return "B"
    return "A"


@dataclass(frozen=True)
class HandoffPacket:
    packet_id: str
    created_at: str
    source: str
    intent_class: str
    target_system: str        # fleet agent name
    target_cli: str           # command-grid alias
    target_model: str
    task: str
    complexity: int
    approval_required: bool
    approval_tier: str
    spoken_update_for_frank: str
    relevant_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "packet_version": 1,
            "packet_id": self.packet_id,
            "created_at": self.created_at,
            "source": self.source,
            "classification": {"intent_class": self.intent_class},
            "target_system": self.target_system,
            "target": {"cli": self.target_cli, "model": self.target_model},
            "task": self.task,
            "complexity": self.complexity,
            "context": {"relevant_files": self.relevant_files},
            "approval": {"required": self.approval_required, "tier": self.approval_tier},
            "spoken_update_for_frank": self.spoken_update_for_frank,
        }


def build_handoff_packet(task: str, *, source: str = "voice", now: datetime | None = None) -> HandoffPacket:
    score = complexity_score(task)
    agent = select_agent(score)
    tier = approval_tier(task)
    stamp = (now or datetime.now(timezone.utc)).isoformat()
    spoken = (
        f"Routing to {agent.name}."
        + ("" if tier == "A" else f" Needs your okay (tier {tier}) before it runs.")
    )
    return HandoffPacket(
        packet_id=str(ulid.new()),
        created_at=stamp,
        source=source,
        intent_class="cli-agent-task",
        target_system=agent.name,
        target_cli=agent.cli,
        target_model=agent.model,
        task=task,
        complexity=score,
        approval_required=(tier != "A"),
        approval_tier=tier,
        spoken_update_for_frank=spoken,
    )


class Dispatcher:
    """Builds packets and (when live) spawns the chosen CLI. Dry-run by default."""

    def __init__(self, *, live: bool = False) -> None:
        self.live = live

    def dispatch(self, task: str, *, source: str = "voice") -> dict[str, object]:
        packet = build_handoff_packet(task, source=source)
        result: dict[str, object] = {"packet": packet.to_dict()}

        if not self.live:
            result["status"] = "dry-run"
            result["note"] = "live=False — packet built, no spawn. Set live=True to execute Tier-A tasks."
            return result

        if packet.approval_required:
            result["status"] = "awaiting-approval"
            result["note"] = f"Tier {packet.approval_tier} — held for Frank's ack before spawn."
            return result

        result["status"] = "spawned" if self._spawn(packet) else "spawn-failed"
        return result

    @staticmethod
    def _spawn(packet: HandoffPacket) -> bool:
        """Fire-and-forget pwsh launch of the target CLI. Never blocks the voice loop."""
        try:
            subprocess.Popen(
                ["pwsh", "-NoProfile", "-Command", f"{packet.target_cli} -p \"{packet.task}\""],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False
