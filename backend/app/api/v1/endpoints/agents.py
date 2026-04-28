from fastapi import APIRouter, HTTPException, status

from app.schemas.agents import AgentRunListResponse
from app.services.agents.run_logger import AgentRunLogger
from app.services.llm.factory import get_llm_provider
from app.services.llm.schemas import LLMProviderInfo

router = APIRouter()


@router.get("/status", response_model=LLMProviderInfo)
def get_agents_status() -> LLMProviderInfo:
    try:
        return get_llm_provider().get_provider_info()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/runs", response_model=AgentRunListResponse)
def list_agent_runs(limit: int = 20) -> AgentRunListResponse:
    return AgentRunListResponse(runs=AgentRunLogger().list_recent(limit=limit))
