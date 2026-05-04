from app.schemas.order import OrderRequest, OrderResponse
from app.services.broker.base import BrokerAdapter
from app.services.connectors.factory import get_account_connector, get_execution_connector


class FutuBrokerAdapter(BrokerAdapter):
    provider_name = "futu"

    def get_positions(self) -> dict[str, float]:
        return get_account_connector("futu").get_positions()

    def get_cash(self) -> float:
        return get_account_connector("futu").get_cash()

    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        connector = get_execution_connector("futu")
        if connector is None:
            raise ValueError("Futu execution connector is unavailable.")
        return connector.submit_order(order_request)

    def cancel_order(self, order_id: str) -> OrderResponse:
        connector = get_execution_connector("futu")
        if connector is None:
            raise ValueError("Futu execution connector is unavailable.")
        return connector.cancel_order(order_id)
