from datetime import UTC, datetime

from app.domain.enums import OrderStatus
from app.schemas.order import OrderRequest, OrderResponse
from app.services.broker.base import BrokerAdapter
from app.services.broker.paper_order_store import PaperOrderStore
from app.services.portfolio.holding_store import PortfolioHoldingStore


class MockBrokerAdapter(BrokerAdapter):
    provider_name = "mock"

    def __init__(
        self,
        paper_order_store: PaperOrderStore | None = None,
        holding_store: PortfolioHoldingStore | None = None,
    ) -> None:
        self._orders: dict[str, OrderResponse] = {}
        self.paper_order_store = paper_order_store or PaperOrderStore()
        self.holding_store = holding_store or PortfolioHoldingStore()

    def get_positions(self) -> dict[str, float]:
        holdings = self.holding_store.list_holdings()
        if holdings:
            return {h.symbol: h.quantity for h in holdings}
        return {"AAPL": 0.12}

    def get_cash(self) -> float:
        return 100_000.0

    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        order_id = f"paper-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}"
        response = OrderResponse(
            order_id=order_id,
            symbol=order_request.symbol.upper(),
            side=order_request.side,
            quantity=order_request.quantity,
            limit_price=order_request.limit_price,
            estimated_amount=order_request.estimated_amount,
            status=OrderStatus.SUBMITTED,
            message="Paper order submitted through MockBrokerAdapter.",
            created_at=datetime.now(UTC),
            broker="mock",
            account_id=order_request.account_id or "paper-default",
            environment=order_request.environment or "paper",
        )
        self._orders[order_id] = response
        self.paper_order_store.save(response)
        self.holding_store.upsert_from_order(response)
        return response

    def cancel_order(self, order_id: str) -> OrderResponse:
        existing = self._orders.get(order_id)
        if existing is None:
            return OrderResponse(
                order_id=order_id,
                symbol="UNKNOWN",
                side="BUY",
                quantity=0.01,
                limit_price=None,
                estimated_amount=0.01,
                status=OrderStatus.REJECTED,
                message="Paper order not found.",
                created_at=datetime.now(UTC),
            )
        cancelled = existing.model_copy(
            update={"status": OrderStatus.CANCELLED, "message": "Paper order cancelled."}
        )
        self._orders[order_id] = cancelled
        return cancelled
