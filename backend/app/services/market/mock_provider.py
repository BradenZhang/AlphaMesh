from datetime import UTC, date, datetime, timedelta

from app.domain.enums import OrderStatus
from app.schemas.market import (
    AccountSnapshot,
    FundamentalsResponse,
    KlineBar,
    KlineResponse,
    QuoteResponse,
)
from app.schemas.order import OrderRequest, OrderResponse
from app.services.market.base import MarketSkillProvider


class MockSkillProvider(MarketSkillProvider):
    provider_name = "mock"

    def get_quote(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(
            symbol=symbol.upper(),
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
        )

    def get_account_snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            cash=100_000.0,
            portfolio_value=150_000.0,
            positions={"AAPL": 0.12},
            provider=self.provider_name,
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
        )
