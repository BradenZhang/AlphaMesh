from fastapi.testclient import TestClient

from app.main import app


def test_memory_api_write_context_stats_and_compact() -> None:
    client = TestClient(app)
    symbol = "MEMAPI"

    write_response = client.post(
        "/api/v1/agents/memory/write",
        json={
            "scope": "short_term",
            "memory_type": "preference",
            "symbol": symbol,
            "content": "Prefer lower drawdown strategies when reviewing MEMAPI.",
            "importance_score": 0.7,
        },
    )
    assert write_response.status_code == 200

    context_response = client.get(f"/api/v1/agents/memory/context?symbol={symbol}")
    stats_response = client.get("/api/v1/agents/memory/stats")
    recent_response = client.get("/api/v1/agents/memory/recent?limit=5")
    compact_response = client.post(f"/api/v1/agents/memory/compact?symbol={symbol}")

    assert context_response.status_code == 200
    assert "lower drawdown" in context_response.json()["context"]
    assert stats_response.status_code == 200
    assert stats_response.json()["total_count"] >= 1
    assert recent_response.status_code == 200
    assert len(recent_response.json()) >= 1
    assert compact_response.status_code == 200
    assert compact_response.json()["scope"] == "long_term"


def test_memory_api_query_stats_and_reload_index() -> None:
    client = TestClient(app)
    symbol = "MEMCN"

    write_response = client.post(
        "/api/v1/agents/memory/write",
        json={
            "scope": "long_term",
            "memory_type": "preference",
            "symbol": symbol,
            "content": "长期记忆偏好：低回撤、估值安全边际、现金流稳定。",
            "importance_score": 0.8,
        },
    )
    assert write_response.status_code == 200
    assert write_response.json()["token_keywords"]

    context_response = client.get(
        f"/api/v1/agents/memory/context?symbol={symbol}&query=低回撤"
    )
    stats_response = client.get("/api/v1/agents/memory/stats")
    reload_response = client.post("/api/v1/agents/memory/reload-index")

    assert context_response.status_code == 200
    assert context_response.json()["query"] == "低回撤"
    assert "低回撤" in context_response.json()["context"]
    assert stats_response.status_code == 200
    assert stats_response.json()["index_loaded_count"] >= 1
    assert stats_response.json()["index_keyword_count"] >= 1
    assert reload_response.status_code == 200
    assert reload_response.json()["index_loaded_count"] >= 1
