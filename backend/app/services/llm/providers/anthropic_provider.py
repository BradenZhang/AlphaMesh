from langchain_anthropic import ChatAnthropic

from app.services.llm.base import LLMProvider
from app.services.llm.providers.langchain_messages import to_langchain_messages
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("anthropic provider requires an API key.")
        self.model = model
        self.client = ChatAnthropic(model=model, api_key=api_key)

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        response = self.client.bind(temperature=temperature).invoke(to_langchain_messages(messages))
        content = response.content if isinstance(response.content, str) else str(response.content)
        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            raw=content,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="anthropic", model=self.model, is_mock=False)
