from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from time import perf_counter


@dataclass(frozen=True)
class BrowserResult:
    ok: bool
    mode: str
    goal: str
    message: str
    elapsed_ms: int

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "goal": self.goal,
            "message": self.message,
            "elapsed_ms": self.elapsed_ms,
        }


class BrowserAutomationAdapter:
    """Browser-use seam.

    The repo must be useful on a fresh laptop before optional browser automation
    dependencies are installed. Dry-run mode validates routing without opening a
    browser. Live mode is intentionally gated on browser-use being installed.
    """

    def __init__(self, *, live: bool = False) -> None:
        self.live = live

    def run(self, goal: str) -> BrowserResult:
        started = perf_counter()
        clean_goal = " ".join(goal.split())
        if not clean_goal:
            return BrowserResult(False, "validation", goal, "Browser goal is empty.", 0)

        if not self.live:
            return BrowserResult(
                True,
                "dry-run",
                clean_goal,
                "Browser task accepted. Install sidecar[browser] and pass --live to execute.",
                self._elapsed(started),
            )

        if find_spec("browser_use") is None:
            return BrowserResult(
                False,
                "missing-dependency",
                clean_goal,
                "browser-use is not installed. Run: uv pip install -e .[browser]",
                self._elapsed(started),
            )

        return BrowserResult(
            False,
            "live-not-wired",
            clean_goal,
            "browser-use is installed, but live execution is not enabled until credential and sandbox policy land.",
            self._elapsed(started),
        )

    @staticmethod
    def _elapsed(started: float) -> int:
        return int((perf_counter() - started) * 1000)
