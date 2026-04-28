from typing import Literal

from pydantic import BaseModel, Field

LLMRole = Literal["system", "user", "assistant"]


class LLMMessage(BaseModel):
    role: LLMRole
    content: str


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
    raw: str | None = None


class LLMProviderInfo(BaseModel):
    provider: str
    model: str
    is_mock: bool = False
