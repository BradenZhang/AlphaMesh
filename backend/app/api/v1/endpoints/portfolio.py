from fastapi import APIRouter, HTTPException

from app.schemas.agents import MultiAgentResearchReport
from app.schemas.portfolio import (
    PortfolioHoldingSchema,
    PortfolioSummary,
    RebalanceRunRequest,
    RebalanceWorkflowResult,
    WatchlistItemCreate,
    WatchlistItemSchema,
    WatchlistResponse,
)
from app.services.portfolio.batch_research import BatchResearchService
from app.services.portfolio.holding_store import PortfolioHoldingStore
from app.services.portfolio.portfolio_service import PortfolioService
from app.services.portfolio.rebalance_workflow import RebalanceWorkflow
from app.services.portfolio.watchlist_store import WatchlistStore

router = APIRouter()
_watchlist = WatchlistStore()
_holdings = PortfolioHoldingStore()
_portfolio = PortfolioService()


# ── Watchlist ──────────────────────────────────────────────


@router.get("/watchlist", response_model=WatchlistResponse)
def list_watchlist(user_id: str = "default") -> WatchlistResponse:
    return WatchlistResponse(items=_watchlist.list_items(user_id))


@router.post("/watchlist", response_model=WatchlistItemSchema)
def add_to_watchlist(item: WatchlistItemCreate, user_id: str = "default") -> WatchlistItemSchema:
    try:
        return _watchlist.add(item, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/watchlist/{item_id}")
def remove_from_watchlist(item_id: str, user_id: str = "default") -> dict[str, bool]:
    removed = _watchlist.remove(item_id, user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    return {"ok": True}


# ── Portfolio ──────────────────────────────────────────────


@router.get("/summary", response_model=PortfolioSummary)
def get_portfolio_summary(user_id: str = "default") -> PortfolioSummary:
    return _portfolio.get_summary(user_id)


@router.get("/holdings", response_model=list[PortfolioHoldingSchema])
def list_holdings(user_id: str = "default") -> list[PortfolioHoldingSchema]:
    return _holdings.list_holdings(user_id)


# ── Research + Rebalance ──────────────────────────────────


@router.post("/watchlist/research")
def batch_research(user_id: str = "default") -> dict[str, MultiAgentResearchReport]:
    items = _watchlist.list_items(user_id)
    symbols = [item.symbol for item in items]
    if not symbols:
        raise HTTPException(status_code=400, detail="Watchlist is empty.")
    service = BatchResearchService()
    return service.run_all(symbols)


@router.post("/rebalance/run", response_model=RebalanceWorkflowResult)
def run_rebalance(request: RebalanceRunRequest) -> RebalanceWorkflowResult:
    workflow = RebalanceWorkflow()
    return workflow.run(request)
