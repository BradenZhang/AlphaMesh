from app.core.config import get_settings
from app.services.broker.base import BrokerAdapter
from app.services.broker.futu_broker import FutuBrokerAdapter
from app.services.broker.ibkr_broker import IbkrBrokerAdapter
from app.services.broker.longbridge_broker import LongbridgeBrokerAdapter
from app.services.broker.mock_broker import MockBrokerAdapter

_BROKER_REGISTRY: dict[str, type[BrokerAdapter]] = {
    "mock": MockBrokerAdapter,
    "longbridge": LongbridgeBrokerAdapter,
    "futu": FutuBrokerAdapter,
    "ibkr": IbkrBrokerAdapter,
}


def get_broker_adapter(name: str | None = None) -> BrokerAdapter:
    settings = get_settings()
    normalized = (name or settings.default_execution_provider).lower().strip()
    adapter_cls = _BROKER_REGISTRY.get(normalized)
    if adapter_cls is None:
        available = ", ".join(sorted(_BROKER_REGISTRY))
        raise ValueError(f"Unknown broker provider '{normalized}'. Available: {available}")
    return adapter_cls()
