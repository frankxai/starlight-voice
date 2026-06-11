from starlight_voice.browser import BrowserAutomationAdapter


def test_browser_dry_run_accepts_goal() -> None:
    result = BrowserAutomationAdapter().run("open the Starlight docs")

    assert result.ok is True
    assert result.mode == "dry-run"
    assert "Starlight docs" in result.goal


def test_browser_rejects_empty_goal() -> None:
    result = BrowserAutomationAdapter().run("  ")

    assert result.ok is False
    assert result.mode == "validation"
