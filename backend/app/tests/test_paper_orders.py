from fastapi.testclient import TestClient

from app.domain.enums import AutomationMode
from app.main import app


def test_paper_auto_persists_order_and_orders_api_lists_it() -> None:
    client = TestClient(app)

    automation_response = client.post(
        "/api/v1/automation/run",
        json={
            "symbol": "MSFT",
            "mode": AutomationMode.PAPER_AUTO,
            "strategy_name": "moving_average_cross",
        },
    )
    assert automation_response.status_code == 200
    order = automation_response.json()["order"]
    assert order is not None

    orders_response = client.get("/api/v1/orders/paper?limit=10")

    assert orders_response.status_code == 200
    orders = orders_response.json()["orders"]
    assert any(saved_order["order_id"] == order["order_id"] for saved_order in orders)
