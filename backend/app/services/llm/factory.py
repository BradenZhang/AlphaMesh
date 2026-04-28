from app.core.config import Settings, get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.providers.mock_provider import MockLLMProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider_name = settings.llm_provider.lower()

    if provider_name == "mock":
        return MockLLMProvider(model=settings.llm_model_name)

    if provider_name in {"openai", "openai_compatible", "deepseek", "qwen"}:
        from app.services.llm.providers.openai_compatible_provider import (
            OpenAICompatibleProvider,
        )

        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key or settings.llm_api_key,
            model=settings.llm_model_name,
            base_url=settings.llm_base_url,
            provider_name=provider_name,
        )

    if provider_name == "anthropic":
        from app.services.llm.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key or settings.llm_api_key,
            model=settings.llm_model_name,
        )

    if provider_name == "gemini":
        from app.services.llm.providers.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.gemini_api_key or settings.llm_api_key,
            model=settings.llm_model_name,
        )

    supported = "mock, openai, openai_compatible, deepseek, qwen, anthropic, gemini"
    raise ValueError(f"Unsupported LLM_PROVIDER '{settings.llm_provider}'. Supported: {supported}.")
