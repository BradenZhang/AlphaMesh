from fastapi import APIRouter

from app.schemas.backtest import BacktestResult, BacktestRunRequest
from app.services.backtest.engine import BacktestEngine
from app.services.market.mock_provider import MockSkillProvider

router = APIRouter()
market_provider = MockSkillProvider()
engine = BacktestEngine()


@router.post("/run", response_model=BacktestResult)
def run_backtest(request: BacktestRunRequest) -> BacktestResult:
    bars = request.bars or market_provider.get_kline(request.symbol).bars
    return engine.run(
        symbol=request.symbol,
        bars=bars,
        strategy_name=request.strategy_name,
        initial_cash=request.initial_cash,
    )
