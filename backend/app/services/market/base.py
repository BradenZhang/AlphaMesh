from abc import ABC, abstractmethod
from datetime import date

from app.schemas.market import AccountSnapshot, FundamentalsResponse, KlineResponse, QuoteResponse
from app.schemas.order import OrderRequest, OrderResponse


class MarketSkillProvider(ABC):
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
    def get_account_snapshot(self) -> AccountSnapshot:
        raise NotImplementedError

    @abstractmethod
    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        raise NotImplementedError


class ExternalMarketProviderStub(MarketSkillProvider):
    provider_name = "external_stub"

    def get_quote(self, symbol: str) -> QuoteResponse:
        raise NotImplementedError(f"{self.provider_name} is not implemented in the MVP scaffold.")

    def get_kline(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> KlineResponse:
        raise NotImplementedError(f"{self.provider_name} is not implemented in the MVP scaffold.")

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        raise NotImplementedError(f"{self.provider_name} is not implemented in the MVP scaffold.")

    def get_account_snapshot(self) -> AccountSnapshot:
        raise NotImplementedError(f"{self.provider_name} is not implemented in the MVP scaffold.")

    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        raise NotImplementedError(f"{self.provider_name} is not implemented in the MVP scaffold.")
