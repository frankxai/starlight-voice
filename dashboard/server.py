from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
RATINGS = ROOT / "ratings.jsonl"
MAX_BODY = 64 * 1024  # reject oversized POSTs (memory-DoS guard)


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:  # security headers on every response
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def log_message(self, *args) -> None:  # quiet by default
        pass

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/healthz":
            self._json(200, {"ok": True, "service": "starlight-voice-dashboard"})
            return
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/ratings":
            self.send_error(404, "Not found")
            return

        try:
            length = int(self.headers.get("content-length", "0"))
        except ValueError:
            self.send_error(400, "Bad content-length")
            return
        if length <= 0 or length > MAX_BODY:
            self.close_connection = True  # don't read the oversized body; signal close cleanly
            self.send_error(413, "Payload too large")
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Invalid JSON")
            return

        record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "source": "starlight-voice-dashboard",
            "payload": payload,
        }
        try:
            with RATINGS.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as e:
            self._json(500, {"ok": False, "error": f"write failed: {e}"})
            return

        self._json(200, {"ok": True, "path": str(RATINGS)})

    def _json(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_server(port: int | None = None) -> ThreadingHTTPServer:
    port = port if port is not None else int(os.environ.get("STARLIGHT_DASHBOARD_PORT", "8765"))
    return ThreadingHTTPServer(("127.0.0.1", port), DashboardHandler)


def main() -> None:
    server = make_server()
    host, port = server.server_address
    print(f"Starlight Voice dashboard: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
