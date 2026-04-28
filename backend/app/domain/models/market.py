from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    timestamp: datetime


@dataclass(frozen=True)
class Kline:
    symbol: str
    timestamp: date
    open: float
    high: float
    low: float
    close: float
    volume: int
