from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.harness import (
    AgentTaskSchema,
    BackgroundRunDetailResponse,
    BackgroundRunSchema,
    BackgroundRunStartRequest,
    TaskCreateRequest,
    TaskListResponse,
    TaskUpdateRequest,
)
from app.services.harness.background import background_run_store
from app.services.harness.tasks import AgentTaskStore

router = APIRouter()
_task_store = AgentTaskStore()


@router.post("/", response_model=AgentTaskSchema)
def create_task(request: TaskCreateRequest) -> AgentTaskSchema:
    return _task_store.create(request)


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    ready: bool = False,
) -> TaskListResponse:
    return TaskListResponse(tasks=_task_store.list(status=status_filter, ready=ready))


@router.get("/{task_id}", response_model=AgentTaskSchema)
def get_task(task_id: str) -> AgentTaskSchema:
    task = _task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.patch("/{task_id}", response_model=AgentTaskSchema)
def update_task(task_id: str, request: TaskUpdateRequest) -> AgentTaskSchema:
    task = _task_store.update(task_id, request)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.post("/{task_id}/start", response_model=BackgroundRunSchema)
def start_task(task_id: str, request: BackgroundRunStartRequest) -> BackgroundRunSchema:
    task = _task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    if task.status not in {"pending", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task '{task_id}' cannot be started from status '{task.status}'.",
        )
    if task.blocked_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task '{task_id}' is blocked by {task.blocked_by}.",
        )
    return background_run_store.start(request, task_id=task_id)


@router.post("/background-runs", response_model=BackgroundRunSchema)
def start_background_run(request: BackgroundRunStartRequest) -> BackgroundRunSchema:
    return background_run_store.start(request)


@router.get("/background-runs/{background_run_id}", response_model=BackgroundRunDetailResponse)
def get_background_run(background_run_id: str) -> BackgroundRunDetailResponse:
    run = background_run_store.get(background_run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Background run '{background_run_id}' not found.",
        )
    return run
