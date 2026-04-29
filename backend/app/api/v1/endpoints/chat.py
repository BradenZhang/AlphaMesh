from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import (
    ChatReplyRequest,
    ChatReplyResponse,
    ConversationCreateRequest,
    ConversationDetail,
    ConversationListResponse,
    ConversationSummary,
    ConversationUpdateRequest,
)
from app.services.chat.service import ChatConversationNotFoundError, ChatService

router = APIRouter()


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations() -> ConversationListResponse:
    return ConversationListResponse(conversations=ChatService().list_conversations())


@router.post("/conversations", response_model=ConversationSummary)
def create_conversation(request: ConversationCreateRequest) -> ConversationSummary:
    return ChatService().create_conversation(request)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str) -> ConversationDetail:
    try:
        return ChatService().get_conversation(conversation_id)
    except ChatConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/conversations/{conversation_id}", response_model=ConversationSummary)
def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
) -> ConversationSummary:
    try:
        return ChatService().update_conversation(conversation_id, request)
    except ChatConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/conversations/{conversation_id}/reply", response_model=ChatReplyResponse)
def reply(
    conversation_id: str,
    request: ChatReplyRequest,
) -> ChatReplyResponse:
    try:
        return ChatService().reply(conversation_id, request)
    except ChatConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
