import json

from app.core.config import Settings
from app.services.llm.factory import get_llm_provider_for_profile, list_llm_profiles
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


def test_llm_profiles_include_default_mock_profile() -> None:
    profiles = list_llm_profiles(Settings())

    assert profiles.default_profile_id == "mock"
    assert any(profile.id == "mock" and profile.is_default for profile in profiles.profiles)
    assert all("api_key" not in profile.model_dump() for profile in profiles.profiles)


def test_get_llm_provider_for_mock_profile() -> None:
    provider = get_llm_provider_for_profile("mock", Settings())

    provider_info = provider.get_provider_info()
    assert provider_info.provider == "mock"
    assert provider_info.is_mock is True
