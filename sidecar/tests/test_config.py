import os

from starlight_voice.config import load_local_env


def test_load_local_env_reads_env_local_without_overwriting_process_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "process-wins")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    (tmp_path / ".env.local").write_text(
        "OPENAI_API_KEY=file-loses\nELEVENLABS_API_KEY=eleven-test\n",
        encoding="utf-8",
    )

    loaded = load_local_env(tmp_path)

    assert loaded == [tmp_path / ".env.local"]
    assert os.environ["OPENAI_API_KEY"] == "process-wins"
    assert os.environ["ELEVENLABS_API_KEY"] == "eleven-test"
