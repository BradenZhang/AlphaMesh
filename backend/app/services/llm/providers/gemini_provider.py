from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.llm.base import LLMProvider
from app.services.llm.providers.langchain_messages import to_langchain_messages
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None, model: str) -> None:
        if not api_key:
            raise ValueError("gemini provider requires an API key.")
        self.model = model
        self.client = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        response = self.client.bind(temperature=temperature).invoke(to_langchain_messages(messages))
        content = response.content if isinstance(response.content, str) else str(response.content)
        return LLMResponse(
            content=content,
            provider="gemini",
            model=self.model,
            raw=content,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="gemini", model=self.model, is_mock=False)
