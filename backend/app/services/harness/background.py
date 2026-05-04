from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

from app.db.init_db import init_db
from app.db.models import BackgroundRunRecord
from app.db.session import SessionLocal
from app.schemas.automation import AutomationRunResponse
from app.schemas.harness import (
    BackgroundRunDetailResponse,
    BackgroundRunSchema,
    BackgroundRunStartRequest,
)
from app.services.automation.flow import AutomationFlow
from app.services.harness.tasks import AgentTaskStore


class BackgroundRunStore:
    def __init__(self) -> None:
        init_db()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="alphamesh-bg")
        self._tasks = AgentTaskStore()

    def start(
        self,
        request: BackgroundRunStartRequest,
        task_id: str | None = None,
    ) -> BackgroundRunSchema:
        with SessionLocal() as session:
            record = BackgroundRunRecord(
                background_run_id=f"bg-{uuid4().hex}",
                task_id=task_id,
                run_type=request.run_type,
                status="pending",
                input_payload=request.model_dump(mode="json"),
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            schema = self._to_schema(record)

        if task_id:
            self._tasks.mark_status(task_id, "in_progress")
        self._executor.submit(self._run_background, schema.background_run_id, request)
        return schema

    def get(self, background_run_id: str) -> BackgroundRunDetailResponse | None:
        with SessionLocal() as session:
            record = self._get_record(session, background_run_id)
            if record is None:
                return None
            schema = self._to_schema(record)
            automation_result = None
            if record.output_payload and record.run_type == "automation":
                automation_result = AutomationRunResponse.model_validate(record.output_payload)
            return BackgroundRunDetailResponse(
                **schema.model_dump(mode="python"),
                automation_result=automation_result,
            )

    def _run_background(
        self,
        background_run_id: str,
        request: BackgroundRunStartRequest,
    ) -> None:
        self._mark_running(background_run_id)
        try:
            if request.run_type != "automation":
                raise ValueError(f"Unsupported background run type '{request.run_type}'.")
            result = AutomationFlow().run(request.automation_request)
            self._mark_completed(background_run_id, result.model_dump(mode="json"))
        except Exception as exc:
            self._mark_failed(background_run_id, str(exc))

    def _mark_running(self, background_run_id: str) -> None:
        with SessionLocal() as session:
            record = self._get_record(session, background_run_id)
            if record is None:
                return
            record.status = "running"
            record.started_at = datetime.now(UTC).replace(tzinfo=None)
            session.commit()

    def _mark_completed(self, background_run_id: str, output: dict[str, object]) -> None:
        with SessionLocal() as session:
            record = self._get_record(session, background_run_id)
            if record is None:
                return
            record.status = "completed"
            record.output_payload = output
            record.completed_at = datetime.now(UTC).replace(tzinfo=None)
            task_id = record.task_id
            run_id = str(output.get("run_id") or "") or None
            session.commit()
        if task_id:
            self._tasks.mark_status(task_id, "completed", linked_run_id=run_id)

    def _mark_failed(self, background_run_id: str, error: str) -> None:
        with SessionLocal() as session:
            record = self._get_record(session, background_run_id)
            if record is None:
                return
            record.status = "failed"
            record.error_message = error
            record.completed_at = datetime.now(UTC).replace(tzinfo=None)
            task_id = record.task_id
            session.commit()
        if task_id:
            self._tasks.mark_status(task_id, "failed")

    def _get_record(self, session, background_run_id: str) -> BackgroundRunRecord | None:
        return (
            session.query(BackgroundRunRecord)
            .filter(BackgroundRunRecord.background_run_id == background_run_id)
            .one_or_none()
        )

    def _to_schema(self, record: BackgroundRunRecord) -> BackgroundRunSchema:
        return BackgroundRunSchema(
            background_run_id=record.background_run_id,
            task_id=record.task_id,
            run_type=record.run_type,
            status=record.status,
            input_payload=record.input_payload,
            output_payload=record.output_payload,
            error_message=record.error_message,
            started_at=record.started_at,
            completed_at=record.completed_at,
            created_at=record.created_at,
        )


background_run_store = BackgroundRunStore()
