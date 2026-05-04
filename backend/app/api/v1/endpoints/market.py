from datetime import date

from fastapi import APIRouter

from app.api.deps import validate_symbol
from app.schemas.market import KlineResponse, QuoteResponse
from app.services.market.factory import get_market_provider

router = APIRouter()


@router.get("/quote/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str, provider: str | None = None) -> QuoteResponse:
    validated = validate_symbol(symbol)
    return get_market_provider(provider).get_quote(validated)


@router.get("/kline/{symbol}", response_model=KlineResponse)
def get_kline(
    symbol: str,
    start: date | None = None,
    end: date | None = None,
    interval: str = "1d",
    provider: str | None = None,
) -> KlineResponse:
    validated = validate_symbol(symbol)
    return get_market_provider(provider).get_kline(
        symbol=validated,
        start=start,
        end=end,
        interval=interval,
    )
