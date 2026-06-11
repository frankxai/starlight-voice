import json

from starlight_voice.ipc import JsonLineIpcServer
from starlight_voice.pipeline import AgentPipeline


def test_ipc_health() -> None:
    server = JsonLineIpcServer(pipeline=AgentPipeline())

    response = server.handle_line(json.dumps({"id": "1", "method": "health", "params": {}}))

    assert response["ok"] is True
    assert response["result"]["status"] == "ok"


def test_ipc_utterance_routes_browser_task() -> None:
    server = JsonLineIpcServer(pipeline=AgentPipeline())

    response = server.handle_line(json.dumps({"id": "2", "method": "utterance", "params": {"text": "open browser and search"}}))

    assert response["ok"] is True
    assert response["result"]["route"]["tier"] == "tier3-browser"


def test_ipc_rejects_unknown_method() -> None:
    server = JsonLineIpcServer(pipeline=AgentPipeline())

    response = server.handle_line(json.dumps({"id": "3", "method": "nope", "params": {}}))

    assert response["ok"] is False
    assert response["error"]["code"] == "unknown-method"
