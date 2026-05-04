from app.domain.enums import ProviderName
from app.schemas.market import (
    FilingsResponse,
    FundamentalsResponse,
    KlineResponse,
    MacroResponse,
    NewsResponse,
    QuoteResponse,
    SentimentResponse,
)
from app.services.connectors.base import ConnectorHealth, MarketDataConnector


class EastMoneyMarketConnector(MarketDataConnector):
    provider_name = ProviderName.EASTMONEY
    transport = "api"

    def _error(self) -> ValueError:
        return ValueError(
            "EastMoney connector scaffold exists, but the API bridge is not "
            "implemented yet."
        )

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
        return ConnectorHealth(
            provider=self.provider_name,
            capability="market",
            transport=self.transport,
            available=False,
            message=(
                "EastMoney market connector scaffold exists, but the API bridge "
                "is not implemented yet."
            ),
        )
