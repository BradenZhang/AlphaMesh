import json

from app.services.llm.providers.mock_provider import MockLLMProvider
from app.services.llm.schemas import LLMMessage


def test_mock_llm_provider_returns_research_json() -> None:
    provider = MockLLMProvider()

    response = provider.generate(
        [
            LLMMessage(role="system", content="Return research JSON only."),
            LLMMessage(role="user", content="symbol: AAPL"),
        ]
    )
    payload = json.loads(response.content)

    assert response.provider == "mock"
    assert payload["symbol"] == "AAPL"
    assert "summary" in payload
    assert 0 <= payload["confidence_score"] <= 1
