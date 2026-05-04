from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.harness import (
    ApprovalCreateRequest,
    ApprovalListResponse,
    ApprovalRequestSchema,
    ApprovalRespondRequest,
)
from app.services.harness.approvals import ApprovalStore

router = APIRouter()
_approval_store = ApprovalStore()


@router.post("/", response_model=ApprovalRequestSchema)
def create_approval(request: ApprovalCreateRequest) -> ApprovalRequestSchema:
    return _approval_store.create(request)


@router.get("/", response_model=ApprovalListResponse)
def list_approvals(
    status_filter: str | None = Query(default=None, alias="status"),
) -> ApprovalListResponse:
    return ApprovalListResponse(approvals=_approval_store.list(status=status_filter))


@router.get("/{approval_id}", response_model=ApprovalRequestSchema)
def get_approval(approval_id: str) -> ApprovalRequestSchema:
    approval = _approval_store.get(approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    return approval


@router.post("/{approval_id}/respond", response_model=ApprovalRequestSchema)
def respond_approval(
    approval_id: str,
    request: ApprovalRespondRequest,
) -> ApprovalRequestSchema:
    try:
        approval = _approval_store.respond(approval_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if approval is None:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found.")
    return approval
