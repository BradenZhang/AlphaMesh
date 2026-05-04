from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _create_conversation(client: TestClient, symbol: str) -> str:
    response = client.post(
        "/api/v1/chat/conversations",
        json={
            "symbol": symbol,
            "strategy_name": "moving_average_cross",
            "market_provider": "mock",
            "execution_provider": "mock",
            "account_provider": "mock",
        },
    )
    assert response.status_code == 200
    return response.json()["conversation_id"]


def test_chat_conversation_create_list_get_and_patch() -> None:
    client = TestClient(app)
    symbol = f"CHAT{uuid4().hex[:6].upper()}"

    conversation_id = _create_conversation(client, symbol)

    list_response = client.get("/api/v1/chat/conversations")
    detail_response = client.get(f"/api/v1/chat/conversations/{conversation_id}")
    patch_response = client.patch(
        f"/api/v1/chat/conversations/{conversation_id}",
        json={
            "title": "Portfolio Review",
            "symbol": "MSFT",
            "market_provider": "longbridge",
        },
    )

    assert list_response.status_code == 200
    assert any(
        item["conversation_id"] == conversation_id
        for item in list_response.json()["conversations"]
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["symbol"] == symbol
    assert detail_response.json()["market_provider"] == "mock"
    assert detail_response.json()["messages"] == []
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Portfolio Review"
    assert patch_response.json()["symbol"] == "MSFT"
    assert patch_response.json()["market_provider"] == "longbridge"


def test_chat_reply_defaults_to_react_question_flow() -> None:
    client = TestClient(app)
    conversation_id = _create_conversation(client, "AAPL")
    prompt = "Compare current price action and fundamentals for AAPL"

    response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/reply",
        json={"message": prompt},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation"]["title"].startswith("Compare current price action")
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["assistant_message"]["artifacts"][0]["type"] == "react_trace"
    assert prompt in payload["assistant_message"]["content"]


def test_chat_reply_supports_research_action() -> None:
    client = TestClient(app)
    conversation_id = _create_conversation(client, "MSFT")

    response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/reply",
        json={"message": "Run a research pass", "action": "research"},
    )

    assert response.status_code == 200
    artifacts = response.json()["assistant_message"]["artifacts"]
    assert [artifact["type"] for artifact in artifacts] == [
        "multi_agent_report",
        "research_report",
    ]


def test_chat_reply_supports_manual_plan_and_paper_auto() -> None:
    client = TestClient(app)
    conversation_id = _create_conversation(client, "AAPL")

    manual_response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/reply",
        json={"message": "Build a manual plan", "action": "manual_plan"},
    )
    paper_response = client.post(
        f"/api/v1/chat/conversations/{conversation_id}/reply",
        json={"message": "Try a paper order", "action": "paper_auto"},
    )
    detail_response = client.get(f"/api/v1/chat/conversations/{conversation_id}")

    assert manual_response.status_code == 200
    manual_artifacts = manual_response.json()["assistant_message"]["artifacts"]
    assert manual_artifacts[0]["type"] == "automation_result"
    assert paper_response.status_code == 200
    paper_artifacts = paper_response.json()["assistant_message"]["artifacts"]
    assert paper_artifacts[0]["type"] == "automation_result"
    assert any(artifact["type"] == "paper_order" for artifact in paper_artifacts)
    assert detail_response.status_code == 200
    roles = [message["role"] for message in detail_response.json()["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]


def test_chat_reply_rejects_missing_conversation_and_invalid_action() -> None:
    client = TestClient(app)

    missing_response = client.post(
        "/api/v1/chat/conversations/conv-missing/reply",
        json={"message": "Hello"},
    )
    invalid_action_response = client.post(
        f"/api/v1/chat/conversations/{_create_conversation(client, 'AAPL')}/reply",
        json={"message": "Hello", "action": "invalid"},
    )

    assert missing_response.status_code == 404
    assert invalid_action_response.status_code == 422
