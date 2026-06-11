from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sidecar" / "src"))

from starlight_voice.browser import BrowserAutomationAdapter  # noqa: E402
from starlight_voice.cognition import CognitionRouter  # noqa: E402


def measure_router(n: int) -> list[int]:
    router = CognitionRouter()
    samples: list[int] = []
    for _ in range(n):
        started = perf_counter()
        router.decide("open browser and search the docs")
        samples.append(int((perf_counter() - started) * 1000))
    return samples


def measure_browser_dry_run(n: int) -> list[int]:
    adapter = BrowserAutomationAdapter()
    samples: list[int] = []
    for _ in range(n):
        started = perf_counter()
        adapter.run("open the docs")
        samples.append(int((perf_counter() - started) * 1000))
    return samples


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", choices=["router", "browser-dry-run"], default="router")
    parser.add_argument("--n", type=int, default=50)
    args = parser.parse_args()

    samples = measure_router(args.n) if args.probe == "router" else measure_browser_dry_run(args.n)
    p50 = int(statistics.median(samples))
    p95 = int(sorted(samples)[max(0, int(len(samples) * 0.95) - 1)])
    print(f"probe={args.probe} n={args.n} p50_ms={p50} p95_ms={p95} max_ms={max(samples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
