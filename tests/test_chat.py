import pytest

try:
    import fastapi
    from app.main import app
    from fastapi.testclient import TestClient
    import app.api.chat_routes as chat_routes
except ImportError as e:
    pytest.skip(f"Skipping because dependencies are missing: {e}", allow_module_level=True)

@pytest.mark.skipif(not all([fastapi, app, TestClient, chat_routes]), 
                   reason="Required dependencies are missing")
def test_chat_endpoint(monkeypatch):
    def dummy_run_chain(user_input: str, session_id: str = "default"):
        return "dummy response"

    monkeypatch.setattr(chat_routes, "run_chain", dummy_run_chain)
    client = TestClient(app)
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json() == {"response": "dummy response"}
