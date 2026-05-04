from datetime import UTC, date, datetime, timedelta

from app.domain.enums import OrderStatus
from app.schemas.market import (
    AccountSnapshot,
    FilingItem,
    FilingsResponse,
    FundamentalsResponse,
    KlineBar,
    KlineResponse,
    MacroIndicator,
    MacroResponse,
    NewsItem,
    NewsResponse,
    QuoteResponse,
    SentimentResponse,
)
from app.schemas.order import OrderRequest, OrderResponse
from app.services.market.base import MarketSkillProvider


class MockSkillProvider(MarketSkillProvider):
    provider_name = "mock"

    def get_quote(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(
            symbol=symbol.upper(),
            market="US",
            currency="USD",
            provider_symbol=symbol.upper(),
            price=102.5,
            open=100.0,
            high=104.2,
            low=98.7,
            previous_close=99.8,
            volume=1_250_000,
            timestamp=datetime.now(UTC),
            provider=self.provider_name,
        )

    def get_kline(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> KlineResponse:
        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=59))
        bars: list[KlineBar] = []
        current = start_date
        index = 0
        while current <= end_date:
            if current.weekday() < 5:
                base = 90 + index * 0.45
                close = base + (index % 7) * 0.35
                bars.append(
                    KlineBar(
                        symbol=symbol.upper(),
                        timestamp=current,
                        open=base,
                        high=close + 1.2,
                        low=base - 1.1,
                        close=close,
                        volume=900_000 + index * 10_000,
                    )
                )
                index += 1
            current += timedelta(days=1)
        return KlineResponse(
            symbol=symbol.upper(),
            interval=interval,
            bars=bars,
            provider=self.provider_name,
            market="US",
            currency="USD",
            provider_symbol=symbol.upper(),
        )

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        return FundamentalsResponse(
            symbol=symbol.upper(),
            pe_ratio=18.5,
            pb_ratio=2.1,
            revenue_growth=0.16,
            net_margin=0.21,
            debt_to_equity=0.38,
            provider=self.provider_name,
            market="US",
            currency="USD",
            provider_symbol=symbol.upper(),
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            cash=100_000.0,
            portfolio_value=150_000.0,
            positions={"AAPL": 0.12},
            provider=self.provider_name,
            account_id="paper-default",
            broker=self.provider_name,
        )

    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        return OrderResponse(
            order_id=f"paper-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
            symbol=order_request.symbol.upper(),
            side=order_request.side,
            quantity=order_request.quantity,
            limit_price=order_request.limit_price,
            estimated_amount=order_request.estimated_amount,
            status=OrderStatus.SUBMITTED,
            message="Mock market provider accepted paper order.",
            created_at=datetime.now(UTC),
            broker=self.provider_name,
            account_id="paper-default",
            environment="paper",
        )

    def get_filings(self, symbol: str, limit: int = 5) -> FilingsResponse:
        today = date.today()
        return FilingsResponse(
            symbol=symbol.upper(),
            filings=[
                FilingItem(
                    filing_type="10-K",
                    title=f"{symbol.upper()} Annual Report FY{today.year - 1}",
                    date=date(today.year - 1, 12, 31),
                    summary="Mock annual report with stable revenue and controlled expenses.",
                ),
                FilingItem(
                    filing_type="10-Q",
                    title=f"{symbol.upper()} Quarterly Report Q{(today.month - 1) // 3}",
                    date=today - timedelta(days=45),
                    summary="Mock quarterly filing showing continued operating momentum.",
                ),
            ],
            provider=self.provider_name,
        )

    def get_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        now = datetime.now(UTC)
        return NewsResponse(
            symbol=symbol.upper(),
            items=[
                NewsItem(
                    headline=f"{symbol.upper()} maintains guidance in mock earnings call",
                    source="mock_wire",
                    date=now - timedelta(hours=2),
                    sentiment=0.15,
                ),
                NewsItem(
                    headline=f"Analyst firm issues neutral rating on {symbol.upper()}",
                    source="mock_analyst",
                    date=now - timedelta(hours=8),
                    sentiment=-0.05,
                ),
                NewsItem(
                    headline=f"{symbol.upper()} announces mock share buyback program",
                    source="mock_pr",
                    date=now - timedelta(days=1),
                    sentiment=0.2,
                ),
            ],
            provider=self.provider_name,
        )

    def get_macro(self, region: str = "US") -> MacroResponse:
        today = date.today()
        return MacroResponse(
            region=region,
            indicators=[
                MacroIndicator(name="CPI YoY", value=3.2, unit="%", date=today),
                MacroIndicator(name="GDP Growth", value=2.1, unit="%", date=today),
                MacroIndicator(name="Unemployment", value=3.8, unit="%", date=today),
                MacroIndicator(name="Fed Funds Rate", value=5.25, unit="%", date=today),
            ],
            provider=self.provider_name,
        )

    def get_sentiment(self, symbol: str) -> SentimentResponse:
        return SentimentResponse(
            symbol=symbol.upper(),
            score=0.1,
            sources=["mock_social", "mock_news"],
            provider=self.provider_name,
        )
