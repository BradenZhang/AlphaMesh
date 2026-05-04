from enum import StrEnum


class SignalAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AutomationMode(StrEnum):
    MANUAL = "manual"
    PAPER_AUTO = "paper_auto"
    LIVE_AUTO = "live_auto"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class StrategyName(StrEnum):
    MOVING_AVERAGE_CROSS = "moving_average_cross"
    VALUATION_BAND = "valuation_band"


class PortfolioDecisionAction(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REDUCE = "reduce"


class TaskComplexity(StrEnum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ProviderName(StrEnum):
    MOCK = "mock"
    LONGBRIDGE = "longbridge"
    FUTU = "futu"
    EASTMONEY = "eastmoney"
    IBKR = "ibkr"


class ProviderTransport(StrEnum):
    CLI = "cli"
    MCP = "mcp"
    OPEND = "opend"
    API = "api"
    CLIENT_PORTAL = "client_portal"
    TWS = "tws"
