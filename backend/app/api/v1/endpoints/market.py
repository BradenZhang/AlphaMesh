from datetime import date

from fastapi import APIRouter

from app.api.deps import validate_symbol
from app.schemas.market import KlineResponse, QuoteResponse
from app.services.market.mock_provider import MockSkillProvider

router = APIRouter()
provider = MockSkillProvider()


@router.get("/quote/{symbol}", response_model=QuoteResponse)
def get_quote(symbol: str) -> QuoteResponse:
    validated = validate_symbol(symbol)
    return provider.get_quote(validated)


@router.get("/kline/{symbol}", response_model=KlineResponse)
def get_kline(
    symbol: str,
    start: date | None = None,
    end: date | None = None,
    interval: str = "1d",
) -> KlineResponse:
    validated = validate_symbol(symbol)
    return provider.get_kline(symbol=validated, start=start, end=end, interval=interval)
