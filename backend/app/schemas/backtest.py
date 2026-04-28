from pydantic import BaseModel, Field

from app.domain.enums import StrategyName
from app.schemas.market import KlineBar


class BacktestRunRequest(BaseModel):
    symbol: str
    strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS
    initial_cash: float = Field(default=100_000.0, gt=0)
    bars: list[KlineBar] | None = None


class EquityPoint(BaseModel):
    timestamp: str
    equity: float


class BacktestResult(BaseModel):
    symbol: str
    strategy_name: StrategyName
    total_return: float
    max_drawdown: float
    win_rate: float
    sharpe_ratio: float
    trade_count: int
    equity_curve: list[EquityPoint]
