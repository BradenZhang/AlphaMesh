from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MemoryScope = Literal["short_term", "long_term"]
MemoryType = Literal[
    "conversation",
    "preference",
    "research_summary",
    "react_trace",
    "risk_note",
]


class MemoryRecordSchema(BaseModel):
    memory_id: str
    scope: MemoryScope
    memory_type: MemoryType
    symbol: str | None = None
    user_id: str = "default"
    content: str
    content_hash: str | None = None
    token_keywords: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    importance_score: float = Field(ge=0, le=1)
    token_estimate: int = Field(ge=0)
    expires_at: datetime | None = None
    created_at: datetime


class MemoryWriteRequest(BaseModel):
    scope: MemoryScope = "short_term"
    memory_type: MemoryType = "conversation"
    symbol: str | None = None
    user_id: str = "default"
    content: str
    metadata: dict[str, object] = Field(default_factory=dict)
    importance_score: float = Field(default=0.5, ge=0, le=1)
    ttl_seconds: int | None = Field(default=None, gt=0)


class MemorySearchRequest(BaseModel):
    symbol: str | None = None
    user_id: str = "default"
    limit: int = Field(default=20, ge=1, le=100)
    scope: MemoryScope | None = None


class MemoryContextResponse(BaseModel):
    symbol: str | None = None
    user_id: str = "default"
    query: str | None = None
    context: str
    memories: list[MemoryRecordSchema]
    token_budget: int
    token_estimate: int
    compacted: bool = False
    compression_triggered: bool = False
    compression_strategy: str = "direct"
    budget_allocation: dict[str, int] = Field(default_factory=dict)
    compression_token_usage: dict[str, int] = Field(default_factory=dict)


class MemoryStatsResponse(BaseModel):
    short_term_count: int
    long_term_count: int
    total_count: int
    total_token_estimate: int
    index_loaded_count: int = 0
    index_keyword_count: int = 0
    index_loaded_at: str | None = None
