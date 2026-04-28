from abc import ABC, abstractmethod

from app.schemas.order import OrderRequest, OrderResponse


class BrokerAdapter(ABC):
    @abstractmethod
    def get_positions(self) -> dict[str, float]:
        raise NotImplementedError

    @abstractmethod
    def get_cash(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> OrderResponse:
        raise NotImplementedError
