from fastapi import APIRouter

from app.schemas.risk import RiskCheckRequest, RiskResult
from app.services.risk.guard import RiskGuard

router = APIRouter()
guard = RiskGuard()


@router.post("/check", response_model=RiskResult)
def check_risk(request: RiskCheckRequest) -> RiskResult:
    return guard.check(request)
