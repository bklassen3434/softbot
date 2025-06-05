import pytest

fastapi = pytest.importorskip("fastapi")

try:
    from app.main import app
    from fastapi.testclient import TestClient
    import app.api.chat_routes as chat_routes
except Exception as e:  # pragma: no cover - dependency missing
    pytest.skip(f"Skipping because dependencies are missing: {e}")


def test_chat_endpoint(monkeypatch):
    def dummy_run_chain(user_input: str, session_id: str = "default"):
        return "dummy response"

    monkeypatch.setattr(chat_routes, "run_chain", dummy_run_chain)
    client = TestClient(app)
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"response": "dummy response"}
