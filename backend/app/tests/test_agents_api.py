from fastapi.testclient import TestClient

from app.main import app


def test_agents_status_endpoint_uses_mock_provider_by_default() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/agents/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["is_mock"] is True
