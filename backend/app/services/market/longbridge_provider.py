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
from app.services.connectors.factory import (
    get_account_connector,
    get_execution_connector,
    get_market_connector,
)
from app.services.market.base import MarketSkillProvider


class LongbridgeProvider(MarketSkillProvider):
    provider_name = "longbridge"

    def get_quote(self, symbol: str) -> QuoteResponse:
        return get_market_connector(self.provider_name).get_quote(symbol)

    def get_kline(self, symbol: str, start=None, end=None, interval: str = "1d") -> KlineResponse:
        return get_market_connector(self.provider_name).get_kline(
            symbol=symbol,
            start=start,
            end=end,
            interval=interval,
        )

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        return get_market_connector(self.provider_name).get_fundamentals(symbol)

    def get_account_snapshot(self) -> AccountSnapshot:
        return get_account_connector(self.provider_name).get_account_snapshot()

    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        connector = get_execution_connector(self.provider_name)
        if connector is None:
            raise ValueError("Longbridge execution connector is unavailable.")
        return connector.submit_order(order_request)

    def get_filings(self, symbol: str, limit: int = 5) -> FilingsResponse:
        return get_market_connector(self.provider_name).get_filings(symbol, limit=limit)

    def get_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        return get_market_connector(self.provider_name).get_news(symbol, limit=limit)

    def get_macro(self, region: str = "US") -> MacroResponse:
        return get_market_connector(self.provider_name).get_macro(region=region)

    def get_sentiment(self, symbol: str) -> SentimentResponse:
        return get_market_connector(self.provider_name).get_sentiment(symbol)
