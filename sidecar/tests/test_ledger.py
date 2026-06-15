from starlight_voice.cognition.ledger import read_runs, record_run, resolve_relevant_files


def test_record_and_read_roundtrip(tmp_path) -> None:
    p = tmp_path / "r.jsonl"
    packet = {"packet_id": "x1", "target_system": "Claude Code", "approval": {"tier": "A"}, "task": "do x"}
    record_run(packet, "spawned", pid=999, path=p)
    runs = read_runs(path=p)
    assert runs[-1]["status"] == "spawned"
    assert runs[-1]["packet_id"] == "x1"
    assert runs[-1]["target"] == "Claude Code"
    assert runs[-1]["pid"] == 999


def test_read_runs_empty_when_no_file(tmp_path) -> None:
    assert read_runs(path=tmp_path / "nope.jsonl") == []


def test_resolve_relevant_files(tmp_path, monkeypatch) -> None:
    repo = tmp_path / "FrankX"
    (repo / ".git").mkdir(parents=True)
    monkeypatch.setenv("STARLIGHT_BRIEF_REPOS", str(repo))
    assert str(repo) in resolve_relevant_files("refactor the frankx auth module")
    assert resolve_relevant_files("do something unrelated to any repo") == []


def test_dispatch_records_to_ledger(tmp_path, monkeypatch) -> None:
    from starlight_voice.cognition.dispatch import Dispatcher

    monkeypatch.setenv("STARLIGHT_RUNS_FILE", str(tmp_path / "runs.jsonl"))
    Dispatcher(live=False).dispatch("read the project layout")
    runs = read_runs(path=tmp_path / "runs.jsonl")
    assert runs and runs[-1]["status"] == "dry-run"  # every dispatch is audited
