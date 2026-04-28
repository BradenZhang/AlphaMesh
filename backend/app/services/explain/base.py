from abc import ABC, abstractmethod

from app.schemas.backtest import BacktestResult
from app.schemas.research import ResearchReport
from app.schemas.risk import RiskResult
from app.schemas.strategy import StrategySignal


class SignalExplainerBase(ABC):
    @abstractmethod
    def explain(
        self,
        research_report: ResearchReport,
        strategy_signal: StrategySignal,
        backtest_result: BacktestResult,
        risk_result: RiskResult,
    ) -> str:
        raise NotImplementedError
