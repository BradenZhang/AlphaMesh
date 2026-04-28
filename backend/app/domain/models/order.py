from dataclasses import dataclass

from app.domain.enums import OrderSide, OrderStatus


@dataclass(frozen=True)
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    estimated_amount: float
    status: OrderStatus
