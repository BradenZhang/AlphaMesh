from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    automation,
    backtest,
    health,
    market,
    orders,
    research,
    risk,
    strategy,
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
