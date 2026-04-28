from fastapi import APIRouter, HTTPException, status

from app.schemas.agents import (
    AgentRunListResponse,
    LLMCallListResponse,
    MultiAgentResearchReport,
    ReActRunRequest,
    ReActRunResponse,
)
from app.schemas.memory import (
    MemoryContextResponse,
    MemoryRecordSchema,
    MemoryStatsResponse,
    MemoryWriteRequest,
)
from app.schemas.research import ResearchAnalyzeRequest
from app.services.agents.react_runtime import ReActRuntime
from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.runtime import AgentRuntime
from app.services.llm.call_logger import LLMCallLogger
from app.services.llm.factory import (
    get_llm_provider,
    get_llm_provider_for_profile,
    list_llm_profiles,
)
from app.services.llm.schemas import LLMProfileListResponse, LLMProviderInfo
from app.services.memory.index import get_memory_index
from app.services.memory.store import MemoryStore

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


@router.get("/llm-calls", response_model=LLMCallListResponse)
def list_llm_calls(limit: int = 20) -> LLMCallListResponse:
    return LLMCallListResponse(calls=LLMCallLogger().list_recent(limit=limit))


@router.get("/llm-profiles", response_model=LLMProfileListResponse)
def get_llm_profiles() -> LLMProfileListResponse:
    try:
        return list_llm_profiles()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/research/workflow", response_model=MultiAgentResearchReport)
def run_multi_agent_research(request: ResearchAnalyzeRequest) -> MultiAgentResearchReport:
    try:
        provider = get_llm_provider_for_profile(request.llm_profile_id)
        return MultiAgentResearchWorkflow(runtime=AgentRuntime(llm_provider=provider)).run(
            request.symbol
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/react/run", response_model=ReActRunResponse)
def run_react_agent(request: ReActRunRequest) -> ReActRunResponse:
    try:
        provider = get_llm_provider_for_profile(request.llm_profile_id)
        return ReActRuntime(llm_provider=provider).run(
            symbol=request.symbol,
            question=request.question,
            llm_profile_id=request.llm_profile_id,
            max_steps=request.max_steps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/memory/context", response_model=MemoryContextResponse)
def get_memory_context(
    symbol: str | None = None,
    query: str | None = None,
) -> MemoryContextResponse:
    return MemoryStore().search_context(symbol=symbol, query=query)


@router.get("/memory/recent", response_model=list[MemoryRecordSchema])
def list_recent_memories(limit: int = 20) -> list[MemoryRecordSchema]:
    return MemoryStore().list_recent(limit=limit)


@router.post("/memory/write", response_model=MemoryRecordSchema)
def write_memory(request: MemoryWriteRequest) -> MemoryRecordSchema:
    return MemoryStore().write(request)


@router.post("/memory/compact", response_model=MemoryRecordSchema)
def compact_memory(symbol: str | None = None) -> MemoryRecordSchema:
    return MemoryStore().compact(symbol=symbol)


@router.get("/memory/stats", response_model=MemoryStatsResponse)
def get_memory_stats() -> MemoryStatsResponse:
    return MemoryStore().stats()


@router.post("/memory/reload-index", response_model=MemoryStatsResponse)
def reload_memory_index() -> MemoryStatsResponse:
    get_memory_index().load_long_term_memories()
    return MemoryStore().stats()
