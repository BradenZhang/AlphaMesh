from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import LiveTradingDisabledError
from app.schemas.automation import AutomationRunRequest, AutomationRunResponse
from app.services.automation.flow import AutomationFlow

router = APIRouter()


@router.post("/run", response_model=AutomationRunResponse)
def run_automation(request: AutomationRunRequest) -> AutomationRunResponse:
    try:
        return AutomationFlow().run(request)
    except LiveTradingDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
