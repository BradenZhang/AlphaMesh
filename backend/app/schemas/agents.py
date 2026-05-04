from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import RunStep
from app.schemas.research import ResearchReport


class AgentRunRecordSchema(BaseModel):
    run_id: str
    run_type: str
    status: str
    symbol: str | None = None
    provider: str | None = None
    model: str | None = None
    input_payload: dict | None = None
    output_payload: dict | None = None
    error_message: str | None = None
    latency_ms: int
    created_at: datetime
    market_provider: str | None = None
    execution_provider: str | None = None
    account_provider: str | None = None


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunRecordSchema]


class LLMCallRecordSchema(BaseModel):
    call_id: str
    call_type: str
    symbol: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    metadata: dict | None = None
    latency_ms: int
    estimated_cost_usd: float = 0.0
    created_at: datetime


class LLMCallListResponse(BaseModel):
    calls: list[LLMCallRecordSchema]


class AgentFinding(BaseModel):
    agent_name: str
    symbol: str
    thesis: str
    key_points: list[str]
    metrics: dict[str, float | str] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
    data_sources: list[str] = Field(default_factory=list)


class InvestmentCommitteeReport(BaseModel):
    symbol: str
    summary: str
    consensus_view: str
    key_debates: list[str]
    action_bias: str
    confidence_score: float = Field(ge=0, le=1)


class MultiAgentResearchReport(BaseModel):
    symbol: str
    findings: list[AgentFinding]
    committee_report: InvestmentCommitteeReport
    research_report: ResearchReport
    case_id: str | None = None
    market_provider: str | None = None


class StrategyReviewReport(BaseModel):
    symbol: str
    aligned: bool
    review_summary: str
    strengths: list[str]
    concerns: list[str]
    confidence_score: float = Field(ge=0, le=1)


class RiskReviewReport(BaseModel):
    symbol: str
    approved_for_auto: bool
    review_summary: str
    risk_flags: list[str]
    confidence_score: float = Field(ge=0, le=1)


class AgentReviewBundle(BaseModel):
    strategy_review: StrategyReviewReport
    risk_review: RiskReviewReport


class ReActToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, object] = Field(default_factory=dict)


class ReActObservation(BaseModel):
    success: bool
    summary: str
    data: dict[str, object] = Field(default_factory=dict)


class ReActStep(BaseModel):
    step_number: int
    rationale_summary: str
    tool_call: ReActToolCall
    observation: ReActObservation


class ReActRunRequest(BaseModel):
    symbol: str
    question: str | None = None
    llm_profile_id: str | None = None
    market_provider: str | None = None
    max_steps: int = Field(default=3, ge=1, le=5)


class ReActRunResponse(BaseModel):
    symbol: str
    llm_profile_id: str | None = None
    steps: list[ReActStep]
    final_answer: str
    confidence_score: float = Field(ge=0, le=1)
    run_steps: list[RunStep] = Field(default_factory=list)
    market_provider: str | None = None


class ProviderHealthSchema(BaseModel):
    provider: str
    capability: str
    transport: str
    available: bool
    message: str | None = None


class ProviderHealthListResponse(BaseModel):
    providers: list[ProviderHealthSchema]
