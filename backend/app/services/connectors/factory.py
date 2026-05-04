from app.core.config import get_settings
from app.domain.enums import ProviderName
from app.services.connectors.base import (
    AccountConnector,
    ConnectorHealth,
    ExecutionConnector,
    MarketDataConnector,
)
from app.services.connectors.eastmoney import EastMoneyMarketConnector
from app.services.connectors.futu import (
    FutuAccountConnector,
    FutuExecutionConnector,
    FutuMarketConnector,
)
from app.services.connectors.ibkr import (
    IbkrAccountConnector,
    IbkrExecutionConnector,
    IbkrMarketConnector,
)
from app.services.connectors.longbridge import (
    LongbridgeAccountConnector,
    LongbridgeExecutionConnector,
    LongbridgeMarketConnector,
)
from app.services.market.mock_provider import MockSkillProvider


class _MockMarketConnector(MarketDataConnector):
    def __init__(self) -> None:
        self.provider = MockSkillProvider()

    def get_quote(self, symbol: str):
        return self.provider.get_quote(symbol)

    def get_kline(self, symbol: str, start=None, end=None, interval: str = "1d"):
        return self.provider.get_kline(symbol=symbol, start=start, end=end, interval=interval)

    def get_fundamentals(self, symbol: str):
        return self.provider.get_fundamentals(symbol)

    def get_filings(self, symbol: str, limit: int = 5):
        return self.provider.get_filings(symbol, limit=limit)

    def get_news(self, symbol: str, limit: int = 10):
        return self.provider.get_news(symbol, limit=limit)

    def get_macro(self, region: str = "US"):
        return self.provider.get_macro(region=region)

    def get_sentiment(self, symbol: str):
        return self.provider.get_sentiment(symbol)

    def healthcheck(self) -> ConnectorHealth:
        return ConnectorHealth(
            provider=ProviderName.MOCK,
            capability="market",
            transport="in_process",
            available=True,
            message="Built-in mock market provider is available.",
        )


class _MockAccountConnector(AccountConnector):
    def __init__(self) -> None:
        self.provider = MockSkillProvider()

    def get_positions(self) -> dict[str, float]:
        return self.provider.get_account_snapshot().positions

    def get_cash(self) -> float:
        return self.provider.get_account_snapshot().cash

    def get_account_snapshot(self):
        return self.provider.get_account_snapshot()

    def healthcheck(self) -> ConnectorHealth:
        return ConnectorHealth(
            provider=ProviderName.MOCK,
            capability="account",
            transport="in_process",
            available=True,
            message="Built-in mock account provider is available.",
        )


_MARKET_CONNECTORS: dict[str, type[MarketDataConnector]] = {
    ProviderName.MOCK: _MockMarketConnector,
    ProviderName.LONGBRIDGE: LongbridgeMarketConnector,
    ProviderName.FUTU: FutuMarketConnector,
    ProviderName.EASTMONEY: EastMoneyMarketConnector,
    ProviderName.IBKR: IbkrMarketConnector,
}

_EXECUTION_CONNECTORS: dict[str, type[ExecutionConnector]] = {
    ProviderName.LONGBRIDGE: LongbridgeExecutionConnector,
    ProviderName.FUTU: FutuExecutionConnector,
    ProviderName.IBKR: IbkrExecutionConnector,
}

_ACCOUNT_CONNECTORS: dict[str, type[AccountConnector]] = {
    ProviderName.MOCK: _MockAccountConnector,
    ProviderName.LONGBRIDGE: LongbridgeAccountConnector,
    ProviderName.FUTU: FutuAccountConnector,
    ProviderName.IBKR: IbkrAccountConnector,
}


def get_market_connector(name: str | None = None) -> MarketDataConnector:
    settings = get_settings()
    normalized = (name or settings.default_market_provider).lower().strip()
    connector_cls = _MARKET_CONNECTORS.get(normalized)
    if connector_cls is None:
        available = ", ".join(sorted(_MARKET_CONNECTORS))
        raise ValueError(f"Unknown market provider '{normalized}'. Available: {available}")
    return connector_cls()


def get_execution_connector(name: str | None = None) -> ExecutionConnector | None:
    settings = get_settings()
    normalized = (name or settings.default_execution_provider).lower().strip()
    connector_cls = _EXECUTION_CONNECTORS.get(normalized)
    if connector_cls is None:
        return None
    return connector_cls()


def get_account_connector(name: str | None = None) -> AccountConnector:
    settings = get_settings()
    normalized = (name or settings.default_account_provider).lower().strip()
    connector_cls = _ACCOUNT_CONNECTORS.get(normalized)
    if connector_cls is None:
        available = ", ".join(sorted(_ACCOUNT_CONNECTORS))
        raise ValueError(f"Unknown account provider '{normalized}'. Available: {available}")
    return connector_cls()


def list_provider_health() -> list[ConnectorHealth]:
    reports: list[ConnectorHealth] = []
    for connector_cls in _MARKET_CONNECTORS.values():
        reports.append(connector_cls().healthcheck())
    for connector_cls in _EXECUTION_CONNECTORS.values():
        reports.append(connector_cls().healthcheck())
    for connector_cls in _ACCOUNT_CONNECTORS.values():
        reports.append(connector_cls().healthcheck())
    return reports
