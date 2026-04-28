from pydantic import BaseModel

from app.domain.enums import AutomationMode, StrategyName
from app.schemas.agents import AgentReviewBundle, MultiAgentResearchReport
from app.schemas.backtest import BacktestResult
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
