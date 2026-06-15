"""Bind the fleet to Frank's REAL config — memory/agent-sessions.json — not a hardcoded tuple.

Survey wf_a7eec750: agent-sessions.json (machine -> repo -> {agent, command, abs path, role}) is
the authoritative fleet map that restart-all-agents.ps1 already reads. The operator must read the
SAME source so voice dispatch targets the right repo, on the right machine, with the configured
agent/command — and respects the 2-laptop role split (DESKTOP-1B4ICID primary / DEFAULT_SECONDARY field).
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _sessions_path() -> Path:
    sis = os.environ.get("STARLIGHT_SIS_ROOT")
    roots = [Path(sis)] if sis else []
    roots.append(Path.home() / "Starlight-Intelligence-System")
    for r in roots:
        p = r / "memory" / "agent-sessions.json"
        if p.exists():
            return p
    return roots[-1] / "memory" / "agent-sessions.json"


def load_sessions() -> dict:
    try:
        return json.loads(_sessions_path().read_text(encoding="utf-8"))
    except Exception:
        return {"machines": {}}


def current_machine() -> str:
    """COMPUTERNAME if it's in the config, else the DEFAULT_SECONDARY (field-laptop) profile."""
    machines = load_sessions().get("machines", {})
    name = os.environ.get("COMPUTERNAME", "")
    return name if name in machines else "DEFAULT_SECONDARY"


def repos(machine: str | None = None) -> list[dict]:
    """[{name, path, agent, command, role}] for this machine (the real per-repo targeting)."""
    machines = load_sessions().get("machines", {})
    return machines.get(machine or current_machine(), {}).get("auto_start_repos", [])


# agent-sessions.json names the agent (claude/codex/antigravity/opencode); spawn the REAL binary
# with cwd=repo.path rather than the PowerShell profile alias (clsis/agyfx) which isn't on PATH.
AGENT_BINARY = {
    "claude": "claude",
    "codex": "codex",
    "opencode": "opencode",
    "antigravity": "agy",
    "grok": "grok",
    "deepagent": "dcode",
}


def agent_binary(agent_name: str) -> str:
    return AGENT_BINARY.get((agent_name or "").lower(), agent_name or "")


def resolve_repo(task: str) -> dict | None:
    """The repo this task targets, matched by name mention. None if no repo named."""
    t = " ".join(task.lower().split())
    # longest name first so 'arcanea-onchain' wins over 'arcanea'
    for r in sorted(repos(), key=lambda r: len(r.get("name", "")), reverse=True):
        if r.get("name", "").lower() in t:
            return r
    return None
