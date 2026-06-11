from __future__ import annotations

import argparse
import json
import sys

from .browser import BrowserAutomationAdapter
from .config import load_local_env
from .environment import EnvironmentDoctor
from .ipc import JsonLineIpcServer
from .pipeline import AgentPipeline


def main(argv: list[str] | None = None) -> int:
    load_local_env()

    parser = argparse.ArgumentParser(prog="starlight-voice-sidecar")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health", help="Print sidecar health as JSON")
    sub.add_parser("doctor", help="Inspect local machine readiness as JSON")

    say = sub.add_parser("say", help="Run the text-mode cognition path")
    say.add_argument("text", nargs="+")

    browser = sub.add_parser("browser", help="Prepare a browser automation task")
    browser.add_argument("goal", nargs="+")
    browser.add_argument("--live", action="store_true", help="Run live browser automation if optional deps are installed")

    sub.add_parser("serve", help="Run JSON-lines IPC on stdin/stdout")

    args = parser.parse_args(argv)
    pipeline = AgentPipeline()

    if args.command == "health":
        print(json.dumps(pipeline.health(), separators=(",", ":")))
        return 0

    if args.command == "doctor":
        print(json.dumps(EnvironmentDoctor().report(), separators=(",", ":")))
        return 0

    if args.command == "say":
        result = pipeline.process_text(" ".join(args.text))
        print(json.dumps(result, separators=(",", ":")))
        return 0

    if args.command == "browser":
        adapter = BrowserAutomationAdapter(live=args.live)
        result = adapter.run(" ".join(args.goal))
        print(json.dumps(result.to_dict(), separators=(",", ":")))
        return 0 if result.ok else 2

    if args.command == "serve":
        server = JsonLineIpcServer(pipeline=AgentPipeline())
        return server.serve(sys.stdin, sys.stdout)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
