"""Headless construction test for the cloud voice graph.

Skips when the `voice` extra or provider keys are absent (e.g. CI), so it stays green there
while validating real graph assembly locally. Does NOT run audio — see benchmarks for latency.
"""

import os

import pytest

pytest.importorskip("pipecat", reason="voice extra not installed")

_KEYS = ("OPENROUTER_API_KEY", "GROQ_API_KEY", "ELEVENLABS_API_KEY")


@pytest.mark.skipif(
    not all(os.environ.get(k) for k in _KEYS),
    reason="cloud provider keys not set",
)
def test_selftest_assembles_cloud_graph() -> None:
    from starlight_voice.voice_loop import selftest

    result = selftest()
    assert result["ok"] is True
    # pipecat wraps the 6-service chain (stt, router, user, llm, tts, assistant) with Source+Sink = 8
    assert result["pipeline_processors"] == 8
    assert result["stt"] == "groq-openrouter"
    assert result["tts"] == "elevenlabs"
    assert "@cerebras" in result["llm"]  # FAST-tier provider pin present
