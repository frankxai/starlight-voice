"""Hardening tests for the dashboard HTTP server (DoS guard, healthz, write path)."""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_DASH = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(_DASH))
import server as dash  # noqa: E402


@pytest.fixture
def live_server():
    srv = dash.make_server(0)  # ephemeral port
    host, port = srv.server_address
    base = f"http://{host}:{port}"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    # wait for readiness (kills the thread-startup race that made this flaky)
    for _ in range(50):
        try:
            urllib.request.urlopen(base + "/healthz", timeout=1)
            break
        except Exception:
            time.sleep(0.02)
    try:
        yield base
    finally:
        srv.shutdown()


def test_healthz_ok(live_server) -> None:
    resp = urllib.request.urlopen(live_server + "/healthz", timeout=5)
    assert json.loads(resp.read())["ok"] is True
    assert resp.headers["X-Content-Type-Options"] == "nosniff"  # security header present


def test_oversized_post_is_rejected(live_server) -> None:
    # Assert the GUARANTEE (oversized refused), not the transport detail: rejecting a large
    # POST without draining the body can surface as a clean 413 OR a connection abort (the
    # server closes rather than read 64KB+). Both mean the memory-DoS guard fired.
    big = b'{"x":"' + b"a" * 70000 + b'"}'  # > 64KB MAX_BODY
    req = urllib.request.Request(live_server + "/ratings", data=big, method="POST")
    try:
        urllib.request.urlopen(req, timeout=5)
        raise AssertionError("oversized POST must be rejected")
    except urllib.error.HTTPError as exc:
        assert exc.code == 413
    except OSError:
        pass  # connection aborted == refused-without-reading; guard still fired


def test_valid_rating_writes_ok(live_server, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dash, "RATINGS", tmp_path / "r.jsonl")  # don't touch real ratings
    data = json.dumps({"option": "hybrid", "rating": 9}).encode("utf-8")
    req = urllib.request.Request(live_server + "/ratings", data=data, method="POST")
    resp = urllib.request.urlopen(req, timeout=5)
    assert json.loads(resp.read())["ok"] is True
    assert (tmp_path / "r.jsonl").exists()


def test_status_endpoint_returns_live_state(live_server) -> None:
    resp = urllib.request.urlopen(live_server + "/status", timeout=5)
    data = json.loads(resp.read())
    assert "variants" in data and "settings" in data  # cockpit's data source
    assert {v["key"] for v in data["variants"]} == {"component", "openai-realtime", "gemini-live"}


def test_unknown_post_route_404(live_server) -> None:
    req = urllib.request.Request(live_server + "/nope", data=b"{}", method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 404


def test_root_serves_landing(live_server) -> None:
    resp = urllib.request.urlopen(live_server + "/", timeout=5)
    body = resp.read().decode("utf-8")
    assert resp.headers["content-type"].startswith("text/html")
    assert "Starlight Voice" in body and "Launch the console" in body


def test_console_and_shared_tokens_served(live_server) -> None:
    console = urllib.request.urlopen(live_server + "/dashboard/cockpit.html", timeout=5)
    assert "Operator Console" in console.read().decode("utf-8")
    tokens = urllib.request.urlopen(live_server + "/tokens.css", timeout=5)
    assert tokens.headers["content-type"].startswith("text/css")
    assert "--voltage" in tokens.read().decode("utf-8")  # the single source of truth


@pytest.mark.parametrize("bad", ["/server.py", "/.git/config", "/sidecar/pyproject.toml", "/../site/tokens.css"])
def test_disallowed_get_is_fail_closed_404(live_server, bad) -> None:
    # The allowlist must refuse anything not explicitly served — no repo source leaks.
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(live_server + bad, timeout=5)
    assert exc.value.code == 404
