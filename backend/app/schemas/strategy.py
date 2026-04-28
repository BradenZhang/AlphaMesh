from pydantic import BaseModel, Field

from app.domain.enums import SignalAction, StrategyName
from app.schemas.market import FundamentalsResponse, KlineBar
from app.schemas.research import ResearchReport


class StrategySignalRequest(BaseModel):
    symbol: str
    strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS
    bars: list[KlineBar] | None = None
    fundamentals: FundamentalsResponse | None = None
    research_report: ResearchReport | None = None


class StrategySignal(BaseModel):
    symbol: str
    action: SignalAction
    confidence: float = Field(ge=0, le=1)
    reason: str
    suggested_position_pct: float = Field(ge=0, le=1)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    strategy_name: StrategyName
