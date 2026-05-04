from fastapi import APIRouter, HTTPException

from app.schemas.case import (
    InvestmentCaseListResponse,
    InvestmentCaseSchema,
    InvestmentCaseUpdateRequest,
)
from app.services.case.store import InvestmentCaseStore

router = APIRouter()
_store = InvestmentCaseStore()


@router.get("/", response_model=InvestmentCaseListResponse)
def list_cases(symbol: str | None = None, limit: int = 20) -> InvestmentCaseListResponse:
    return InvestmentCaseListResponse(cases=_store.list_recent(symbol=symbol, limit=limit))


@router.get("/{case_id}", response_model=InvestmentCaseSchema)
def get_case(case_id: str) -> InvestmentCaseSchema:
    try:
        return _store.get(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{case_id}", response_model=InvestmentCaseSchema)
def update_case(case_id: str, request: InvestmentCaseUpdateRequest) -> InvestmentCaseSchema:
    try:
        return _store.update_outcome(case_id, outcome=request.outcome or "")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
