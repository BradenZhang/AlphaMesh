from app.core.config import get_settings
from app.services.market.base import MarketSkillProvider
from app.services.market.eastmoney_provider import EastMoneyProvider
from app.services.market.futu_provider import FutuProvider
from app.services.market.ibkr_provider import IBKRProvider
from app.services.market.longbridge_provider import LongbridgeProvider
from app.services.market.mock_provider import MockSkillProvider
from app.services.market.tonghuashun_provider import TongHuaShunProvider

_PROVIDER_REGISTRY: dict[str, type[MarketSkillProvider]] = {
    "mock": MockSkillProvider,
    "longbridge": LongbridgeProvider,
    "futu": FutuProvider,
    "ibkr": IBKRProvider,
    "eastmoney": EastMoneyProvider,
    "tonghuashun": TongHuaShunProvider,
}


def get_market_provider(name: str | None = None) -> MarketSkillProvider:
    settings = get_settings()
    normalized = (name or settings.default_market_provider).lower().strip()
    provider_cls = _PROVIDER_REGISTRY.get(normalized)
    if provider_cls is None:
        available = ", ".join(sorted(_PROVIDER_REGISTRY))
        raise ValueError(f"Unknown market provider '{normalized}'. Available: {available}")
    return provider_cls()
