from abc import ABC, abstractmethod

from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def get_provider_info(self) -> LLMProviderInfo:
        raise NotImplementedError
