from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import AutomationMode, StrategyName
from app.schemas.agents import AgentReviewBundle, MultiAgentResearchReport
from app.schemas.backtest import BacktestResult
from app.schemas.common import RunStep
from app.schemas.market import KlineResponse, QuoteResponse
from app.schemas.order import OrderResponse
from app.schemas.research import ResearchReport
from app.schemas.risk import RiskResult
from app.schemas.strategy import StrategySignal


class AutomationRunRequest(BaseModel):
    symbol: str
    mode: AutomationMode = AutomationMode.MANUAL
    strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS
    llm_profile_id: str | None = None
    market_provider: str | None = None
    execution_provider: str | None = None
    account_provider: str | None = None
    dry_run: bool = False
    slippage_bps: float = Field(default=0.0, ge=0, le=500)
    commission_per_trade: float = Field(default=0.0, ge=0)
    walk_forward: bool = False
    train_ratio: float = Field(default=0.7, gt=0.5, lt=1.0)


class AutomationRunResponse(BaseModel):
    symbol: str
    mode: AutomationMode
    quote: QuoteResponse
    kline: KlineResponse
    research_report: ResearchReport
    strategy_signal: StrategySignal
    backtest_result: BacktestResult
    risk_result: RiskResult
    explanation: str
    multi_agent_report: MultiAgentResearchReport | None = None
    agent_reviews: AgentReviewBundle | None = None
    order: OrderResponse | None = None
    executed: bool = False
    message: str
    run_steps: list[RunStep] = Field(default_factory=list)
    case_id: str | None = None
    run_id: str | None = None
    market_provider: str | None = None
    execution_provider: str | None = None
    account_provider: str | None = None


class RunCheckpointSchema(BaseModel):
    checkpoint_id: str
    run_id: str
    step_id: str
    step_label: str
    status: str
    input_snapshot: dict | None = None
    output_snapshot: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0


class CheckpointListResponse(BaseModel):
    checkpoints: list[RunCheckpointSchema]
