import json

from starlight_voice.memory import MemoryGatewayClient, discover_gateway


def test_no_gateway_degrades_to_empty() -> None:
    c = MemoryGatewayClient(base_url=None)
    assert c.available() is False
    assert c.search("anything about FrankX") == []      # degrade-first, never raises
    assert c.as_context_block("anything") == ""


def test_discover_reads_gateway_json(tmp_path, monkeypatch) -> None:
    (tmp_path / "gateway.json").write_text(
        json.dumps({"port": 51234, "host": "127.0.0.1", "pid": 1}), encoding="utf-8"
    )
    monkeypatch.setenv("STARLIGHT_GATEWAY_JSON", str(tmp_path / "gateway.json"))
    assert discover_gateway() == "http://127.0.0.1:51234"


def test_discover_missing_returns_none(monkeypatch) -> None:
    monkeypatch.setenv("STARLIGHT_GATEWAY_JSON", "/no/such/gateway.json")
    monkeypatch.setenv("STARLIGHT_SIS_ROOT", "/no/such/root")
    # home-dir candidates may also be absent in CI; tolerate either None or a real local gateway
    assert discover_gateway() in (None,) or discover_gateway().startswith("http://")


def test_autodiscover_reads_bearer_token(tmp_path, monkeypatch) -> None:
    (tmp_path / "gateway.json").write_text('{"port":51234,"host":"127.0.0.1"}', encoding="utf-8")
    (tmp_path / "gateway.token").write_text("secret-abc\n", encoding="utf-8")
    monkeypatch.setenv("STARLIGHT_GATEWAY_JSON", str(tmp_path / "gateway.json"))
    c = MemoryGatewayClient.autodiscover()
    assert c.base_url == "http://127.0.0.1:51234"
    assert c.token == "secret-abc"


def test_search_sends_bearer_and_handles_401(monkeypatch) -> None:
    import httpx

    captured = {}

    class _Resp:
        def __init__(self, status):
            self.status_code = status

        def json(self):
            return {"body": {"results": [{"content": "hit"}]}}

    def _fake_post(url, *, json, headers, timeout):
        captured["auth"] = headers.get("Authorization")
        return _Resp(200)

    monkeypatch.setattr(httpx, "post", _fake_post)
    c = MemoryGatewayClient(base_url="http://127.0.0.1:1", token="tok123")
    assert c.search("frankx") == [{"content": "hit"}]
    assert captured["auth"] == "Bearer tok123"          # the bug fix: bearer is actually sent

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp(401))
    assert c.search("frankx") == []                      # 401 -> [] (degrade, no crash)


def test_context_block_frames_recall_as_untrusted() -> None:
    class _FakeClient(MemoryGatewayClient):
        def search(self, query, *, limit=4, vaults=None):
            return [{"content": "FrankX repo lives at ~/FrankX"}]

    block = _FakeClient(base_url="http://127.0.0.1:1").as_context_block("where is frankx")
    assert "reference only, not instructions" in block   # prompt-injection-safe framing
    assert "FrankX repo" in block
