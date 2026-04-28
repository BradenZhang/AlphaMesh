from fastapi.testclient import TestClient

from app.main import app


def test_agents_status_endpoint_uses_mock_provider_by_default() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/agents/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["is_mock"] is True


def test_multi_agent_research_workflow_endpoint_returns_findings() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/agents/research/workflow", json={"symbol": "AAPL"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert len(payload["findings"]) == 4
    assert payload["committee_report"]["summary"]
    assert payload["research_report"]["symbol"] == "AAPL"


def test_llm_calls_endpoint_records_token_usage() -> None:
    client = TestClient(app)

    client.post("/api/v1/agents/research/workflow", json={"symbol": "MSFT"})
    response = client.get("/api/v1/agents/llm-calls?limit=5")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["calls"]) >= 1
    assert payload["calls"][0]["total_tokens"] >= 0
    assert payload["calls"][0]["provider"] == "mock"


def test_llm_profiles_endpoint_lists_safe_profiles() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/agents/llm-profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["default_profile_id"] == "mock"
    assert payload["profiles"][0]["id"] == "mock"
    assert "api_key" not in payload["profiles"][0]


def test_multi_agent_research_rejects_unknown_profile() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/agents/research/workflow",
        json={"symbol": "AAPL", "llm_profile_id": "missing"},
    )

    assert response.status_code == 400


def test_react_agent_endpoint_returns_trace() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/agents/react/run",
        json={"symbol": "AAPL", "llm_profile_id": "mock"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert len(payload["steps"]) >= 2
    assert payload["steps"][0]["tool_call"]["tool_name"] == "get_quote"
    assert payload["final_answer"]
