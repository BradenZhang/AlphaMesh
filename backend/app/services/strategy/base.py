from abc import ABC, abstractmethod

from app.schemas.market import FundamentalsResponse, KlineBar
from app.schemas.research import ResearchReport
from app.schemas.strategy import StrategySignal


class Strategy(ABC):
    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        bars: list[KlineBar] | None = None,
        fundamentals: FundamentalsResponse | None = None,
        research_report: ResearchReport | None = None,
    ) -> StrategySignal:
        raise NotImplementedError
