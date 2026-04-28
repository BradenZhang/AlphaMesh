from app.domain.enums import StrategyName
from app.services.strategy.base import Strategy
from app.services.strategy.moving_average import MovingAverageCrossStrategy
from app.services.strategy.valuation_band import ValuationBandStrategy


def get_strategy(strategy_name: StrategyName) -> Strategy:
    strategies: dict[StrategyName, Strategy] = {
        StrategyName.MOVING_AVERAGE_CROSS: MovingAverageCrossStrategy(),
        StrategyName.VALUATION_BAND: ValuationBandStrategy(),
    }
    return strategies[strategy_name]
