from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import StrategyName

ChatRole = Literal["user", "assistant"]
ReplyAction = Literal["chat", "research", "manual_plan", "paper_auto"]
MessageStatus = Literal["completed", "error"]
ArtifactType = Literal[
    "react_trace",
    "research_report",
    "multi_agent_report",
    "automation_result",
    "paper_order",
]


class ChatArtifactSchema(BaseModel):
    type: ArtifactType
    title: str
    payload: dict[str, object] = Field(default_factory=dict)


class ChatMessageSchema(BaseModel):
    message_id: str
    conversation_id: str
    role: ChatRole
    action: ReplyAction | None = None
    content: str
    artifacts: list[ChatArtifactSchema] = Field(default_factory=list)
    status: MessageStatus = "completed"
    created_at: datetime


class ConversationSummary(BaseModel):
    conversation_id: str
    title: str
    symbol: str | None = None
    llm_profile_id: str | None = None
    strategy_name: StrategyName | None = None
    user_id: str = "default"
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[ChatMessageSchema] = Field(default_factory=list)


class ConversationCreateRequest(BaseModel):
    symbol: str | None = None
    llm_profile_id: str | None = None
    strategy_name: StrategyName | None = None
    user_id: str = "default"


class ConversationUpdateRequest(BaseModel):
    symbol: str | None = None
    llm_profile_id: str | None = None
    strategy_name: StrategyName | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]


class ChatReplyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    action: ReplyAction = "chat"
    symbol: str | None = None
    llm_profile_id: str | None = None
    strategy_name: StrategyName | None = None


class ChatReplyResponse(BaseModel):
    conversation: ConversationSummary
    user_message: ChatMessageSchema
    assistant_message: ChatMessageSchema
