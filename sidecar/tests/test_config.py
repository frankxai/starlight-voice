import os

from starlight_voice.config import Settings, load_local_env


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


def test_settings_defaults_match_validated_stack() -> None:
    s = Settings()
    assert s.stt_engine == "faster-whisper"
    assert s.tts_engine == "kokoro"
    assert s.llm_fast_provider == "cerebras"  # FAST tier must pin a sub-200ms-TTFT provider
    assert s.first_audio_p50_budget_ms == 800
    assert "stt_engine" in s.to_dict()


def test_settings_from_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("STARLIGHT_TTS_ENGINE", "cartesia")
    monkeypatch.setenv("STARLIGHT_STT_DEVICE", "cpu")
    s = Settings.from_env()
    assert s.tts_engine == "cartesia"
    assert s.stt_device == "cpu"
    assert s.stt_engine == "faster-whisper"  # unset -> default


def test_settings_from_env_blank_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("STARLIGHT_TTS_ENGINE", "   ")
    assert Settings.from_env().tts_engine == "kokoro"
