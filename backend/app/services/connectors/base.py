from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from app.schemas.market import (
    AccountSnapshot,
    FilingsResponse,
    FundamentalsResponse,
    KlineResponse,
    MacroResponse,
    NewsResponse,
    QuoteResponse,
    SentimentResponse,
)
from app.schemas.order import OrderRequest, OrderResponse


@dataclass
class ConnectorHealth:
    provider: str
    capability: str
    transport: str
    available: bool
    message: str | None = None


class MarketDataConnector(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> QuoteResponse:
        raise NotImplementedError

    @abstractmethod
    def get_kline(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> KlineResponse:
        raise NotImplementedError

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        raise NotImplementedError

    @abstractmethod
    def get_filings(self, symbol: str, limit: int = 5) -> FilingsResponse:
        raise NotImplementedError

    @abstractmethod
    def get_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        raise NotImplementedError

    @abstractmethod
    def get_macro(self, region: str = "US") -> MacroResponse:
        raise NotImplementedError

    @abstractmethod
    def get_sentiment(self, symbol: str) -> SentimentResponse:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> ConnectorHealth:
        raise NotImplementedError


class ExecutionConnector(ABC):
    @abstractmethod
    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResponse:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> ConnectorHealth:
        raise NotImplementedError


class AccountConnector(ABC):
    @abstractmethod
    def get_positions(self) -> dict[str, float]:
        raise NotImplementedError

    @abstractmethod
    def get_cash(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_account_snapshot(self) -> AccountSnapshot:
        raise NotImplementedError

    @abstractmethod
    def healthcheck(self) -> ConnectorHealth:
        raise NotImplementedError
