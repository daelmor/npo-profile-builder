"""Scaffold smoke test: the app constructs and basic routes respond."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_responds() -> None:
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
