from app.domain.enums import ProviderName
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
from app.services.connectors.base import (
    AccountConnector,
    ConnectorHealth,
    ExecutionConnector,
    MarketDataConnector,
)


class _UnavailableMixin:
    provider_name = ProviderName.FUTU
    transport = "opend"

    def _error(self) -> ValueError:
        return ValueError(
            "Futu connector scaffold exists, but the OpenD integration is not "
            "implemented yet."
        )

    def healthcheck(self, capability: str) -> ConnectorHealth:
        return ConnectorHealth(
            provider=self.provider_name,
            capability=capability,
            transport=self.transport,
            available=False,
            message="Futu connector scaffold exists, but the OpenD bridge is not implemented yet.",
        )


class FutuMarketConnector(_UnavailableMixin, MarketDataConnector):
    def get_quote(self, symbol: str) -> QuoteResponse:
        raise self._error()

    def get_kline(self, symbol: str, start=None, end=None, interval: str = "1d") -> KlineResponse:
        raise self._error()

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        raise self._error()

    def get_filings(self, symbol: str, limit: int = 5) -> FilingsResponse:
        raise self._error()

    def get_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        raise self._error()

    def get_macro(self, region: str = "US") -> MacroResponse:
        raise self._error()

    def get_sentiment(self, symbol: str) -> SentimentResponse:
        raise self._error()

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("market")


class FutuExecutionConnector(_UnavailableMixin, ExecutionConnector):
    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        raise self._error()

    def cancel_order(self, order_id: str) -> OrderResponse:
        raise self._error()

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("execution")


class FutuAccountConnector(_UnavailableMixin, AccountConnector):
    def get_positions(self) -> dict[str, float]:
        raise self._error()

    def get_cash(self) -> float:
        raise self._error()

    def get_account_snapshot(self) -> AccountSnapshot:
        raise self._error()

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("account")
