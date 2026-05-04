import time

from fastapi.testclient import TestClient

from app.main import app


def test_task_graph_clears_dependencies_when_parent_completes() -> None:
    client = TestClient(app)

    parent = client.post("/api/v1/tasks/", json={"subject": "Research AAPL"}).json()
    child = client.post(
        "/api/v1/tasks/",
        json={
            "subject": "Review AAPL risk",
            "blocked_by": [parent["task_id"]],
        },
    ).json()

    assert child["status"] == "blocked"

    response = client.patch(
        f"/api/v1/tasks/{parent['task_id']}",
        json={"status": "completed"},
    )

    assert response.status_code == 200
    refreshed = client.get(f"/api/v1/tasks/{child['task_id']}").json()
    assert refreshed["status"] == "pending"
    assert refreshed["blocked_by"] == []


def test_approval_request_response_fsm() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/approvals/",
        json={
            "request_type": "execution_approval",
            "subject": "Approve paper order",
            "requested_by": "risk_agent",
            "payload": {"symbol": "AAPL", "side": "BUY"},
        },
    ).json()

    assert created["status"] == "pending"

    response = client.post(
        f"/api/v1/approvals/{created['approval_id']}/respond",
        json={"approve": True, "reason": "Paper-only approval."},
    )

    assert response.status_code == 200
    approved = response.json()
    assert approved["status"] == "approved"
    assert approved["reason"] == "Paper-only approval."

    second_response = client.post(
        f"/api/v1/approvals/{created['approval_id']}/respond",
        json={"approve": False},
    )
    assert second_response.status_code == 400


def test_background_automation_run_updates_task() -> None:
    client = TestClient(app)

    task = client.post("/api/v1/tasks/", json={"subject": "Run AAPL plan"}).json()
    response = client.post(
        f"/api/v1/tasks/{task['task_id']}/start",
        json={
            "run_type": "automation",
            "automation_request": {
                "symbol": "AAPL",
                "mode": "manual",
                "strategy_name": "moving_average_cross",
            },
        },
    )

    assert response.status_code == 200
    background_run_id = response.json()["background_run_id"]

    detail = None
    for _ in range(20):
        detail = client.get(f"/api/v1/tasks/background-runs/{background_run_id}").json()
        if detail["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)

    assert detail is not None
    assert detail["status"] == "completed"
    assert detail["automation_result"]["symbol"] == "AAPL"
    refreshed_task = client.get(f"/api/v1/tasks/{task['task_id']}").json()
    assert refreshed_task["status"] == "completed"
    assert refreshed_task["linked_run_id"]
