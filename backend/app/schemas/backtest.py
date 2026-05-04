from pydantic import BaseModel, Field

from app.domain.enums import StrategyName
from app.schemas.market import KlineBar


class BacktestRunRequest(BaseModel):
    symbol: str
    strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS
    initial_cash: float = Field(default=100_000.0, gt=0)
    bars: list[KlineBar] | None = None
    slippage_bps: float = Field(default=0.0, ge=0, le=500)
    commission_per_trade: float = Field(default=0.0, ge=0)
    walk_forward: bool = False
    train_ratio: float = Field(default=0.7, gt=0.5, lt=1.0)


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
    slippage_bps: float = 0.0
    commission_per_trade: float = 0.0
    oos_total_return: float | None = None
    oos_max_drawdown: float | None = None
    oos_sharpe_ratio: float | None = None
    is_total_return: float | None = None
    is_max_drawdown: float | None = None
    is_sharpe_ratio: float | None = None
    validation_badge: str | None = None
    look_ahead_bias_check: bool = True
