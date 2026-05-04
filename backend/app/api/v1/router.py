from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    approvals,
    automation,
    backtest,
    cases,
    chat,
    health,
    market,
    orders,
    portfolio,
    research,
    risk,
    strategy,
    tasks,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
