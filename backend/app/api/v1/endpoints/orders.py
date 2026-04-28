from fastapi import APIRouter

from app.schemas.order import PaperOrderListResponse
from app.services.broker.paper_order_store import PaperOrderStore

router = APIRouter()


@router.get("/paper", response_model=PaperOrderListResponse)
def list_paper_orders(limit: int = 20) -> PaperOrderListResponse:
    return PaperOrderListResponse(orders=PaperOrderStore().list_recent(limit=limit))
