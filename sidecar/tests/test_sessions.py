import json
import os

from starlight_voice.cognition.sessions import agent_binary, repos, resolve_repo


def _write_sessions(tmp_path, monkeypatch):
    sis = tmp_path / "sis"
    (sis / "memory").mkdir(parents=True)
    machine = os.environ.get("COMPUTERNAME", "DEFAULT_SECONDARY")
    (sis / "memory" / "agent-sessions.json").write_text(
        json.dumps({
            "machines": {
                machine: {
                    "auto_start_repos": [
                        {"name": "FrankX", "path": str(tmp_path / "FrankX"), "agent": "antigravity", "command": "agyfx", "role": "x"},
                        {"name": "Starlight-Intelligence-System", "path": str(tmp_path / "SIS"), "agent": "claude", "command": "clsis", "role": "y"},
                    ]
                }
            }
        }),
        encoding="utf-8",
    )
    monkeypatch.setenv("STARLIGHT_SIS_ROOT", str(sis))


def test_repos_and_resolve(tmp_path, monkeypatch) -> None:
    _write_sessions(tmp_path, monkeypatch)
    assert {r["name"] for r in repos()} == {"FrankX", "Starlight-Intelligence-System"}
    r = resolve_repo("refactor the frankx auth module")
    assert r and r["name"] == "FrankX" and r["agent"] == "antigravity"
    assert resolve_repo("do something generic with no repo named") is None


def test_agent_binary_maps_to_real_executables() -> None:
    assert agent_binary("claude") == "claude"
    assert agent_binary("antigravity") == "agy"
    assert agent_binary("codex") == "codex"


def test_dispatch_targets_real_repo_path_and_cwd(tmp_path, monkeypatch) -> None:
    _write_sessions(tmp_path, monkeypatch)
    from starlight_voice.cognition.dispatch import build_handoff_packet

    pkt = build_handoff_packet("read the frankx readme").to_dict()
    assert pkt["target_system"] == "FrankX"
    assert pkt["target"]["cwd"].endswith("FrankX")        # spawns in the right tree
    assert pkt["target"]["cli"] == "agy"                  # real binary, not the clsis-style alias
    assert pkt["context"]["relevant_files"] == [str(tmp_path / "FrankX")]
