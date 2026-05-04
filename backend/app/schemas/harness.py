from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.automation import AutomationRunRequest, AutomationRunResponse

PlanStepStatus = Literal["pending", "in_progress", "completed", "blocked", "cancelled"]
TaskStatus = Literal["pending", "in_progress", "completed", "blocked", "cancelled", "failed"]
BackgroundRunStatus = Literal["pending", "running", "completed", "failed"]
ApprovalStatus = Literal["pending", "approved", "rejected", "expired"]
ApprovalType = Literal[
    "plan_approval",
    "execution_approval",
    "risk_exception",
    "provider_health_override",
]


class PlanStepSchema(BaseModel):
    id: str
    text: str
    status: PlanStepStatus = "pending"


class PlanUpdateRequest(BaseModel):
    plan_id: str | None = None
    owner_type: str = "react"
    owner_id: str | None = None
    symbol: str | None = None
    steps: list[PlanStepSchema]


class AgentPlanSchema(BaseModel):
    plan_id: str
    owner_type: str
    owner_id: str | None = None
    symbol: str | None = None
    status: str
    steps: list[PlanStepSchema]
    created_at: datetime
    updated_at: datetime


class TaskCreateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=160)
    description: str | None = None
    blocked_by: list[str] = Field(default_factory=list)
    owner: str | None = None
    linked_case_id: str | None = None
    linked_run_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    status: TaskStatus | None = None
    blocked_by: list[str] | None = None
    owner: str | None = None
    linked_case_id: str | None = None
    linked_run_id: str | None = None
    metadata: dict[str, object] | None = None


class AgentTaskSchema(BaseModel):
    task_id: str
    subject: str
    description: str | None = None
    status: TaskStatus
    blocked_by: list[str] = Field(default_factory=list)
    owner: str | None = None
    linked_case_id: str | None = None
    linked_run_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[AgentTaskSchema]


class BackgroundRunStartRequest(BaseModel):
    run_type: Literal["automation"] = "automation"
    automation_request: AutomationRunRequest


class BackgroundRunSchema(BaseModel):
    background_run_id: str
    task_id: str | None = None
    run_type: str
    status: BackgroundRunStatus
    input_payload: dict[str, object] | None = None
    output_payload: dict[str, object] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class BackgroundRunDetailResponse(BackgroundRunSchema):
    automation_result: AutomationRunResponse | None = None


class ApprovalCreateRequest(BaseModel):
    request_type: ApprovalType
    subject: str = Field(min_length=1, max_length=160)
    requested_by: str = "agent"
    target: str | None = None
    linked_task_id: str | None = None
    linked_run_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    expires_at: datetime | None = None


class ApprovalRespondRequest(BaseModel):
    approve: bool
    reason: str | None = None
    response: dict[str, object] = Field(default_factory=dict)


class ApprovalRequestSchema(BaseModel):
    approval_id: str
    request_type: ApprovalType
    status: ApprovalStatus
    subject: str
    requested_by: str
    target: str | None = None
    linked_task_id: str | None = None
    linked_run_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    response: dict[str, object] = Field(default_factory=dict)
    reason: str | None = None
    expires_at: datetime | None = None
    decided_at: datetime | None = None
    created_at: datetime


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalRequestSchema]
