from fastapi.testclient import TestClient

from app.main import app


def test_agent_runs_endpoint_lists_recent_runs() -> None:
    client = TestClient(app)
    research_response = client.post("/api/v1/research/analyze", json={"symbol": "AAPL"})

    runs_response = client.get("/api/v1/agents/runs?limit=5")

    assert research_response.status_code == 200
    assert runs_response.status_code == 200
    runs = runs_response.json()["runs"]
    assert runs
    assert any(run["run_type"] == "research" and run["symbol"] == "AAPL" for run in runs)
