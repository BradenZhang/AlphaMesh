from fastapi import APIRouter

from app.api.deps import validate_symbol
from app.schemas.strategy import StrategySignal, StrategySignalRequest
from app.services.market.mock_provider import MockSkillProvider
from app.services.strategy.factory import get_strategy

router = APIRouter()
market_provider = MockSkillProvider()


@router.post("/signal", response_model=StrategySignal)
def generate_signal(request: StrategySignalRequest) -> StrategySignal:
    validated = validate_symbol(request.symbol)
    bars = request.bars or market_provider.get_kline(validated).bars
    fundamentals = request.fundamentals or market_provider.get_fundamentals(validated)
    strategy = get_strategy(request.strategy_name)
    return strategy.generate_signal(
        symbol=validated,
        bars=bars,
        fundamentals=fundamentals,
        research_report=request.research_report,
    )
