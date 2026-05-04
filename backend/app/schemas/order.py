from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import OrderSide, OrderStatus


class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: float = Field(gt=0)
    limit_price: float | None = Field(default=None, gt=0)
    estimated_amount: float = Field(gt=0)
    broker: str | None = None
    account_id: str | None = None
    environment: str | None = None
    preview_only: bool = False


class OrderResponse(BaseModel):
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    limit_price: float | None = None
    estimated_amount: float
    status: OrderStatus
    message: str
    created_at: datetime
    paper: bool = True
    broker: str | None = None
    account_id: str | None = None
    environment: str | None = None
    external_order_id: str | None = None
    requires_confirmation: bool = False


class PaperOrderRecordResponse(BaseModel):
    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    limit_price: float | None = None
    estimated_amount: float | None = None
    status: OrderStatus
    created_at: datetime
    paper: bool = True


class PaperOrderListResponse(BaseModel):
    orders: list[PaperOrderRecordResponse]
