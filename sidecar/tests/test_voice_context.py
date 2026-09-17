"""Role-boundary tests that do not require Pipecat or provider credentials."""


def test_recalled_material_is_untrusted_reference_metadata_not_a_conversation_role() -> None:
    from starlight_voice.voice_loop import with_reference_context

    result = with_reference_context({"route_tier": "deliberation"}, "memory result")

    assert result["route_tier"] == "deliberation"
    assert result["reference_context"] == {
        "content": "memory result",
        "trust": "untrusted",
        "source": "sis-memory",
    }
    assert "role" not in result["reference_context"]
