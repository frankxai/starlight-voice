"""Dispatch run-ledger + repo resolution — supervise the agents the operator starts.

Review wf_a9484479: dispatch was fire-and-forget into the void — no record, no way to report
on spawned agents, an always-empty relevant_files. This adds an append-only JSONL ledger
(audit trail written BEFORE/at spawn) and a repo-name resolver so the operator can answer
"what are my agents doing?" and target the right repo.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path


def _default_runs_path() -> Path:
    # sidecar repo root: .../starlight-voice ; co-locate with the morning brief under memory/voice
    return Path(__file__).resolve().parents[3] / "memory" / "voice" / "runs.jsonl"


def runs_path() -> Path:
    env = os.environ.get("STARLIGHT_RUNS_FILE")
    return Path(env) if env else _default_runs_path()


def record_run(packet: dict, status: str, *, pid: int | None = None, path: Path | None = None) -> None:
    """Append-only audit record for a dispatch decision. Never raises into the voice loop."""
    target = path or runs_path()
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "packet_id": packet.get("packet_id"),
        "status": status,
        "target": packet.get("target_system"),
        "tier": packet.get("approval", {}).get("tier"),
        "task": packet.get("task"),
        "pid": pid,
    }
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # audit best-effort; never block dispatch on a log write


def read_runs(limit: int = 20, *, path: Path | None = None) -> list[dict]:
    """Most-recent dispatch records (newest last). Empty if no ledger yet."""
    target = path or runs_path()
    if not target.exists():
        return []
    try:
        lines = [ln for ln in target.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return [json.loads(ln) for ln in lines[-limit:]]
    except (OSError, json.JSONDecodeError):
        return []


def known_repos() -> dict[str, str]:
    """name -> path for repos the operator can target. From STARLIGHT_BRIEF_REPOS, else siblings."""
    env = os.environ.get("STARLIGHT_BRIEF_REPOS", "")
    paths = [Path(p) for p in env.replace(";", ",").split(",") if p.strip()]
    if not paths:
        # default: sibling repos under the parent of this sidecar repo
        parent = Path(__file__).resolve().parents[4]
        paths = [d for d in parent.iterdir() if (d / ".git").exists()] if parent.exists() else []
    return {p.name.lower(): str(p) for p in paths}


def resolve_relevant_files(task: str) -> list[str]:
    """Resolve repo names mentioned in the task to absolute paths (populates the handoff packet)."""
    t = task.lower()
    return [path for name, path in known_repos().items() if name in t]
