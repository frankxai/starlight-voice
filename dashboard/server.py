from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
RATINGS = ROOT / "ratings.jsonl"


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/ratings":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "source": "starlight-voice-dashboard",
            "payload": payload,
        }
        with RATINGS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        body = json.dumps({"ok": True, "path": str(RATINGS)}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), DashboardHandler)
    print("Starlight Voice dashboard: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
