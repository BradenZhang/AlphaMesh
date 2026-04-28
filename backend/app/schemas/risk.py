from pydantic import BaseModel, Field

from app.domain.enums import AutomationMode, RiskLevel
from app.schemas.backtest import BacktestResult
from app.schemas.order import OrderRequest
from app.schemas.strategy import StrategySignal


class RiskCheckRequest(BaseModel):
    signal: StrategySignal
    order_request: OrderRequest | None = None
    backtest_result: BacktestResult | None = None
    portfolio_value: float = Field(default=100_000.0, gt=0)
    current_position_pct: float = Field(default=0.0, ge=0, le=1)
    mode: AutomationMode = AutomationMode.MANUAL


class RiskResult(BaseModel):
    approved: bool
    risk_level: RiskLevel
    reasons: list[str]
