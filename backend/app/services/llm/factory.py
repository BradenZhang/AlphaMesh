import json
import os

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.providers.mock_provider import MockLLMProvider
from app.services.llm.schemas import LLMProfileInfo, LLMProfileListResponse


class _LLMProfileConfig(BaseModel):
    id: str
    label: str
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    is_default: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)


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


def list_llm_profiles(settings: Settings | None = None) -> LLMProfileListResponse:
    settings = settings or get_settings()
    configs = _load_profile_configs(settings)
    default_profile_id = _get_default_profile_id(configs)
    return LLMProfileListResponse(
        default_profile_id=default_profile_id,
        profiles=[
            LLMProfileInfo(
                id=config.id,
                label=config.label,
                provider=config.provider,
                model=config.model,
                base_url_configured=bool(config.base_url),
                api_key_configured=_has_api_key(config, settings),
                is_mock=config.provider.lower() == "mock",
                is_default=config.id == default_profile_id,
            )
            for config in configs
        ],
    )


def get_llm_provider_for_profile(
    profile_id: str | None = None,
    settings: Settings | None = None,
) -> LLMProvider:
    settings = settings or get_settings()
    if not profile_id:
        return get_llm_provider(settings)

    config = _find_profile(profile_id, settings)
    provider_name = config.provider.lower()
    if provider_name == "mock":
        return MockLLMProvider(model=config.model)

    api_key = _get_profile_api_key(config, settings)
    if provider_name in {"openai", "openai_compatible", "deepseek", "qwen"}:
        from app.services.llm.providers.openai_compatible_provider import (
            OpenAICompatibleProvider,
        )

        return OpenAICompatibleProvider(
            api_key=api_key,
            model=config.model,
            base_url=config.base_url,
            provider_name=provider_name,
        )

    if provider_name == "anthropic":
        from app.services.llm.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=api_key, model=config.model)

    if provider_name == "gemini":
        from app.services.llm.providers.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=api_key, model=config.model)

    supported = "mock, openai, openai_compatible, deepseek, qwen, anthropic, gemini"
    raise ValueError(
        f"Unsupported LLM profile provider '{config.provider}'. Supported: {supported}."
    )


def _load_profile_configs(settings: Settings) -> list[_LLMProfileConfig]:
    profiles: dict[str, _LLMProfileConfig] = {}
    if settings.llm_provider.lower() == "mock":
        profiles["mock"] = _LLMProfileConfig(
            id="mock",
            label="Mock LLM",
            provider="mock",
            model=settings.llm_model_name or "mock-research-v1",
            is_default=True,
        )
    else:
        profiles["mock"] = _LLMProfileConfig(
            id="mock",
            label="Mock LLM",
            provider="mock",
            model="mock-research-v1",
        )
        profiles["default"] = _LLMProfileConfig(
            id="default",
            label="Environment Default",
            provider=settings.llm_provider,
            model=settings.llm_model_name,
            base_url=settings.llm_base_url,
            is_default=True,
        )

    for profile in _parse_profiles_json(settings.llm_profiles_json):
        if profile.is_default:
            profiles = {
                key: value.model_copy(update={"is_default": False})
                for key, value in profiles.items()
            }
        profiles[profile.id] = profile

    return list(profiles.values())


def _parse_profiles_json(raw_profiles: str | None) -> list[_LLMProfileConfig]:
    if not raw_profiles:
        return []
    try:
        payload = json.loads(raw_profiles)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM_PROFILES_JSON must be valid JSON.") from exc

    if not isinstance(payload, list):
        raise ValueError("LLM_PROFILES_JSON must be a JSON array.")

    try:
        return [_LLMProfileConfig.model_validate(item) for item in payload]
    except ValidationError as exc:
        raise ValueError(f"Invalid LLM profile configuration: {exc}") from exc


def _get_default_profile_id(configs: list[_LLMProfileConfig]) -> str:
    for config in configs:
        if config.is_default:
            return config.id
    return configs[0].id


def _find_profile(profile_id: str, settings: Settings) -> _LLMProfileConfig:
    for profile in _load_profile_configs(settings):
        if profile.id == profile_id:
            return profile
    raise ValueError(f"Unknown LLM profile '{profile_id}'.")


def _get_profile_api_key(config: _LLMProfileConfig, settings: Settings) -> str | None:
    if config.api_key:
        return config.api_key
    if config.api_key_env:
        return os.getenv(config.api_key_env)

    provider_name = config.provider.lower()
    if provider_name in {"openai", "openai_compatible", "deepseek", "qwen"}:
        return settings.openai_api_key or settings.llm_api_key
    if provider_name == "anthropic":
        return settings.anthropic_api_key or settings.llm_api_key
    if provider_name == "gemini":
        return settings.gemini_api_key or settings.llm_api_key
    return None


def _has_api_key(config: _LLMProfileConfig, settings: Settings) -> bool:
    if config.provider.lower() == "mock":
        return True
    return bool(_get_profile_api_key(config, settings))
