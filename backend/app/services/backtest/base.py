from abc import ABC, abstractmethod

from app.domain.enums import StrategyName
from app.schemas.backtest import BacktestResult
from app.schemas.market import KlineBar


class BacktestRunner(ABC):
    @abstractmethod
    def run(
        self,
        symbol: str,
        bars: list[KlineBar],
        strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS,
        initial_cash: float = 100_000.0,
    ) -> BacktestResult:
        raise NotImplementedError
