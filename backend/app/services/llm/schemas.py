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


class LLMProfileInfo(BaseModel):
    id: str
    label: str
    provider: str
    model: str
    base_url_configured: bool = False
    api_key_configured: bool = False
    is_mock: bool = False
    is_default: bool = False


class LLMProfileListResponse(BaseModel):
    default_profile_id: str
    profiles: list[LLMProfileInfo]
