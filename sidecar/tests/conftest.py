import pytest


@pytest.fixture(autouse=True)
def _isolate_side_effects(tmp_path, monkeypatch):
    """Keep every test's dispatch run-ledger writes off the real repo file."""
    monkeypatch.setenv("STARLIGHT_RUNS_FILE", str(tmp_path / "runs.jsonl"))
