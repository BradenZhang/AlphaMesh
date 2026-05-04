from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import LiveTradingDisabledError
from app.schemas.automation import (
    AutomationRunRequest,
    AutomationRunResponse,
    CheckpointListResponse,
)
from app.services.agents.run_logger import AgentRunLogger
from app.services.automation.checkpoint import CheckpointStore
from app.services.automation.flow import AutomationFlow

router = APIRouter()
_checkpoint_store = CheckpointStore()
_run_logger = AgentRunLogger()


@router.post("/run", response_model=AutomationRunResponse)
def run_automation(request: AutomationRunRequest) -> AutomationRunResponse:
    try:
        return AutomationFlow().run(request)
    except LiveTradingDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/retry/{run_id}", response_model=AutomationRunResponse)
def retry_automation(run_id: str) -> AutomationRunResponse:
    run_record = _run_logger.get_by_run_id(run_id)
    if run_record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    if run_record.input_payload is None:
        raise HTTPException(
            status_code=400,
            detail=f"Run '{run_id}' has no input payload to retry.",
        )
    try:
        request = AutomationRunRequest.model_validate(run_record.input_payload)
        return AutomationFlow().run(request, run_id=run_id, resume=True)
    except LiveTradingDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/replay/{run_id}", response_model=AutomationRunResponse)
def replay_automation(run_id: str) -> AutomationRunResponse:
    run_record = _run_logger.get_by_run_id(run_id)
    if run_record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    if run_record.input_payload is None:
        raise HTTPException(
            status_code=400,
            detail=f"Run '{run_id}' has no input payload to replay.",
        )
    try:
        request = AutomationRunRequest.model_validate(run_record.input_payload)
        return AutomationFlow().run(request, run_id=run_id, replay=True)
    except LiveTradingDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/checkpoints/{run_id}", response_model=CheckpointListResponse)
def list_checkpoints(run_id: str) -> CheckpointListResponse:
    return CheckpointListResponse(checkpoints=_checkpoint_store.get_all(run_id))
