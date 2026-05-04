from datetime import date, datetime

from pydantic import BaseModel, Field


class QuoteResponse(BaseModel):
    symbol: str
    market: str | None = None
    currency: str | None = None
    provider_symbol: str | None = None
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
    market: str | None = None
    currency: str | None = None
    provider_symbol: str | None = None


class FundamentalsResponse(BaseModel):
    symbol: str
    pe_ratio: float
    pb_ratio: float
    revenue_growth: float
    net_margin: float
    debt_to_equity: float
    provider: str
    market: str | None = None
    currency: str | None = None
    provider_symbol: str | None = None


class AccountSnapshot(BaseModel):
    cash: float
    portfolio_value: float
    positions: dict[str, float]
    provider: str
    account_id: str | None = None
    broker: str | None = None


class FilingItem(BaseModel):
    filing_type: str
    title: str
    date: date
    url: str | None = None
    summary: str


class FilingsResponse(BaseModel):
    symbol: str
    filings: list[FilingItem]
    provider: str


class NewsItem(BaseModel):
    headline: str
    source: str
    date: datetime
    url: str | None = None
    sentiment: float | None = Field(default=None, ge=-1, le=1)


class NewsResponse(BaseModel):
    symbol: str
    items: list[NewsItem]
    provider: str


class MacroIndicator(BaseModel):
    name: str
    value: float
    unit: str
    date: date


class MacroResponse(BaseModel):
    region: str
    indicators: list[MacroIndicator]
    provider: str


class SentimentResponse(BaseModel):
    symbol: str
    score: float = Field(ge=-1, le=1)
    sources: list[str]
    provider: str
