from langchain_anthropic import ChatAnthropic

from app.services.llm.base import LLMProvider, _make_retry_decorator
from app.services.llm.providers.langchain_messages import to_langchain_messages
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        api_key: str | None,
        model: str,
        timeout: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("anthropic provider requires an API key.")
        self.model = model
        self.client = ChatAnthropic(model=model, api_key=api_key, timeout=timeout)
        self._retry_decorator = _make_retry_decorator(max_retries)

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        @self._retry_decorator
        def _invoke():
            return self._timed_call(
                f"anthropic({self.model})",
                self.client.bind(temperature=temperature).invoke,
                to_langchain_messages(messages),
            )

        response = _invoke()
        content = response.content if isinstance(response.content, str) else str(response.content)
        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            usage=self._extract_usage(response),
            raw=content,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="anthropic", model=self.model, is_mock=False)

    def _extract_usage(self, response) -> dict[str, int]:
        usage = getattr(response, "usage_metadata", None) or {}
        return {
            "prompt_tokens": int(usage.get("input_tokens") or 0),
            "completion_tokens": int(usage.get("output_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }
