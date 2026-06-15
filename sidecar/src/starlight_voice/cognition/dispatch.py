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
from datetime import UTC, datetime

import ulid

from .fleet import select_agent

# Tier doctrine (PRD §4) — DEFAULT-DENY (review wf_a9484479: a deny-list keyword gate is
# fail-OPEN — it missed "nuke the prod database" and false-blocked "merge sort"). The gate's
# job is to PAUSE and read the resolved command back for confirmation, NOT to judge safety by
# wordlist. So: Tier A is granted ONLY on positive read-only signal with no mutation marker;
# everything else needs ack; ALWAYS-ASK items hard-block even with a generic ack.
#   A free  — provably read-only, runs immediately
#   B ack   — anything mutating (default) -> spoken read-back + Frank ack
#   C stop  — substrate/sovereignty -> escalate to board
#   D block — CLAUDE.md ALWAYS-ASK -> hard stop, never auto-runs even with generic ack
_ALWAYS_ASK = (
    "rotate", "force push", "force-push", "reset --hard", "drop table", "drop database",
    "wipe prod", "wipe production", "nuke", "send email", "email blast", "stripe", "charge",
    "refund", "payment", "business/", "papa/", "delete database", "factory reset",
)
_SUBSTRATE = ("substrate", "sip protocol", "sovereignty", "schema migration", "breaking change")
_READONLY_LEAD = (
    "read", "show", "list", "summarize", "explain", "search", "find", "check", "status",
    "diff", "log", "what", "analyze", "review", "describe", "print", "tell me", "how ",
)
_MUTATION = (
    "write", "delete", "remove", "push", "merge", "deploy", "publish", "create", "modify",
    "edit", "run", "install", "rm ", "drop", "reset", "rename", "move", "commit", "refactor",
    "fix", "update", "add", "build", "send", "rotate", "kill", "stop",
)


def approval_tier(task: str) -> str:
    t = " ".join(task.lower().split())
    if any(k in t for k in _ALWAYS_ASK):
        return "D"
    if any(k in t for k in _SUBSTRATE):
        return "C"
    # Tier A only on POSITIVE read-only signal AND no mutation marker anywhere (default-deny).
    leads_readonly = any(t == v or t.startswith(v + " ") for v in _READONLY_LEAD)
    if leads_readonly and not any(m in t for m in _MUTATION):
        return "A"
    return "B"


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


def build_handoff_packet(
    task: str, *, source: str = "voice", now: datetime | None = None, classifier=None
) -> HandoffPacket:
    # ONE classification (LLM structured-output when a classifier is injected, else keyword
    # fail-closed). Lazy import breaks the classify<->dispatch cycle.
    from .classify import classify

    c = classify(task, llm_call=classifier)
    score, tier = c.complexity, c.approval_tier
    agent = select_agent(score)
    stamp = (now or datetime.now(UTC)).isoformat()
    if tier == "D":
        spoken = f"Blocked: that's an always-ask action. I will not run \"{task}\" without your explicit go-ahead."
    elif tier == "A":
        spoken = f"Routing to {agent.name}."
    else:
        spoken = f"Routing to {agent.name}, but I'll read it back for your okay first (tier {tier})."
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

        # Tier D = CLAUDE.md ALWAYS-ASK — hard stop, never auto-runs even live, even with generic ack.
        if packet.approval_tier == "D":
            result["status"] = "hard-blocked"
            result["note"] = "ALWAYS-ASK action — requires Frank's explicit, specific go-ahead. Never auto-runs."
            return result

        if not self.live:
            result["status"] = "dry-run"
            result["note"] = "live=False — packet built, no spawn. Set live=True to execute Tier-A tasks."
            return result

        if packet.approval_required:
            result["status"] = "awaiting-approval"
            result["note"] = f"Tier {packet.approval_tier} — held for Frank's spoken read-back + ack before spawn."
            return result

        result["status"] = "spawned" if self._spawn(packet) else "spawn-failed"
        return result

    @staticmethod
    def _spawn(packet: HandoffPacket) -> bool:
        """Launch the target CLI as inert argv — NO shell, NO -Command string.

        Security (review wf_a9484479): the old path f-stringed raw voice transcript into
        `pwsh -Command`, an injection sink. Here `task` is one argv element the OS never
        re-parses (shell=False); the CLI is resolved on PATH via an allow-list (unresolvable
        alias -> refuse, never fall back to a shell). stdout/stderr go to a per-run log.
        """
        import shutil
        from pathlib import Path

        exe = shutil.which(packet.target_cli)
        if exe is None:
            return False  # alias not a resolvable executable -> refuse (do NOT shell-resolve)
        if len(packet.task) > 2000 or any(ord(c) < 32 and c != "\t" for c in packet.task):
            return False  # reject oversized / control-char payloads

        runs_dir = Path(__file__).resolve().parents[3] / "memory" / "voice" / "runs"
        try:
            runs_dir.mkdir(parents=True, exist_ok=True)
            log = open(runs_dir / f"{packet.packet_id}.log", "w", encoding="utf-8")
            subprocess.Popen([exe, "-p", packet.task], stdout=log, stderr=subprocess.STDOUT, shell=False)
            return True
        except Exception:
            return False
