from fastapi import APIRouter

from app.api.deps import validate_symbol
from app.schemas.backtest import BacktestResult, BacktestRunRequest
from app.services.backtest.engine import BacktestEngine
from app.services.market.mock_provider import MockSkillProvider

router = APIRouter()
market_provider = MockSkillProvider()
engine = BacktestEngine()


@router.post("/run", response_model=BacktestResult)
def run_backtest(request: BacktestRunRequest) -> BacktestResult:
    validated = validate_symbol(request.symbol)
    bars = request.bars or market_provider.get_kline(validated).bars
    return engine.run(
        symbol=validated,
        bars=bars,
        strategy_name=request.strategy_name,
        initial_cash=request.initial_cash,
        slippage_bps=request.slippage_bps,
        commission_per_trade=request.commission_per_trade,
        walk_forward=request.walk_forward,
        train_ratio=request.train_ratio,
    )
