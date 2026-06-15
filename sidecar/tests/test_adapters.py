import pytest

from starlight_voice import adapters


def test_availability_reports_every_known_engine_as_bool() -> None:
    avail = adapters.availability()
    assert set(avail) == set(adapters._ENGINE_IMPORTS)
    assert all(isinstance(v, bool) for v in avail.values())


def test_require_unknown_engine_raises_with_known_list() -> None:
    with pytest.raises(adapters.VoiceDepsUnavailable) as exc:
        adapters.require("not-a-real-engine")
    assert "Unknown engine" in str(exc.value)


def test_require_missing_engine_gives_install_hint(monkeypatch) -> None:
    # force the engine's import to look absent
    monkeypatch.setattr(adapters, "_present", lambda name: False)
    with pytest.raises(adapters.VoiceDepsUnavailable) as exc:
        adapters.require("kokoro")
    assert adapters.INSTALL_HINT in str(exc.value)


def test_protocols_are_runtime_checkable() -> None:
    # an object with the right method satisfies the Protocol
    class FakeStt:
        def transcribe(self, pcm: bytes, sample_rate: int) -> str:
            return "ok"

    assert isinstance(FakeStt(), adapters.SttEngine)
