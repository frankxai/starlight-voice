from starlight_voice.pipeline import AgentPipeline


def test_health_declares_current_capabilities() -> None:
    health = AgentPipeline().health()

    assert health["status"] == "ok"
    assert health["capabilities"]["text_mode"] is True
    assert health["capabilities"]["voice_loop"] is False


def test_default_text_path_is_alive() -> None:
    result = AgentPipeline().process_text("hello")

    assert result["route"]["tier"] == "tier1-fast"
    assert result["response"]["type"] == "voice"
