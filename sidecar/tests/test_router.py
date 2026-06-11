from starlight_voice.cognition import CognitionRouter


def test_router_detects_control() -> None:
    decision = CognitionRouter().decide("pause")

    assert decision.tier == "tier0-control"


def test_router_detects_browser_task() -> None:
    decision = CognitionRouter().decide("open browser and click the login button")

    assert decision.tier == "tier3-browser"


def test_router_detects_cli_agent_task() -> None:
    decision = CognitionRouter().decide("ask codex to run tests")

    assert decision.tier == "tier3-cli-agent"


def test_router_detects_deliberation() -> None:
    decision = CognitionRouter().decide("think hard about the architecture tradeoff")

    assert decision.tier == "tier25-deliberation"
