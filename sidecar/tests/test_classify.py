from starlight_voice.cognition.classify import Classification, classify


def test_control_prefilter_no_llm_roundtrip() -> None:
    # unambiguous control word resolves deterministically, never calls the LLM
    def _boom(_):
        raise AssertionError("LLM must not be called for control words")

    c = classify("pause", llm_call=_boom)
    assert c.route_tier == "control"
    assert c.source == "control-prefilter"


def test_llm_path_used_when_valid() -> None:
    def _llm(_prompt):
        return {
            "route_tier": "cli-agent", "complexity": 8, "approval_tier": "B",
            "intent_class": "refactor", "requires_ack": True, "rationale": "multi-file edit",
        }

    c = classify("refactor the auth module", llm_call=_llm)
    assert c.source == "llm"
    assert c.complexity == 8
    assert c.approval_tier == "B"


def test_llm_failure_fails_closed_to_keyword() -> None:
    def _llm(_prompt):
        raise TimeoutError("model slow")

    c = classify("delete the old branches", llm_call=_llm)
    assert c.source == "fail-closed-keyword"
    assert c.approval_tier in {"B", "C", "D"}   # uncertainty never auto-runs (A)


def test_invalid_llm_output_rejected_and_fails_closed() -> None:
    def _llm(_prompt):
        return {"route_tier": "WAT", "complexity": 99, "approval_tier": "Z"}  # violates schema

    c = classify("do something", llm_call=_llm)
    assert c.source == "fail-closed-keyword"     # junk rejected, not trusted


def test_destructive_stays_tier_d_even_without_llm() -> None:
    c = classify("rotate the production API key", llm_call=None)
    assert c.approval_tier == "D"                # ALWAYS-ASK survives the fallback path
    assert isinstance(c, Classification)
