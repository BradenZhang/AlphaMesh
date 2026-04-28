from datetime import date, datetime

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    open: float
    high: float
    low: float
    previous_close: float
    volume: int
    timestamp: datetime
    provider: str


class KlineBar(BaseModel):
    symbol: str
    timestamp: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class KlineResponse(BaseModel):
    symbol: str
    interval: str
    bars: list[KlineBar]
    provider: str


class FundamentalsResponse(BaseModel):
    symbol: str
    pe_ratio: float
    pb_ratio: float
    revenue_growth: float
    net_margin: float
    debt_to_equity: float
    provider: str


class AccountSnapshot(BaseModel):
    cash: float
    portfolio_value: float
    positions: dict[str, float]
    provider: str
