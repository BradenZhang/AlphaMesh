from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.models import AgentTaskRecord
from app.db.session import SessionLocal
from app.schemas.harness import AgentTaskSchema, TaskCreateRequest, TaskUpdateRequest


class AgentTaskStore:
    def __init__(self) -> None:
        init_db()

    def create(self, request: TaskCreateRequest) -> AgentTaskSchema:
        with SessionLocal() as session:
            now = datetime.now(UTC).replace(tzinfo=None)
            record = AgentTaskRecord(
                task_id=f"task-{uuid4().hex}",
                subject=request.subject,
                description=request.description,
                status="blocked" if request.blocked_by else "pending",
                blocked_by=request.blocked_by,
                owner=request.owner,
                linked_case_id=request.linked_case_id,
                linked_run_id=request.linked_run_id,
                metadata_payload=request.metadata,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def list(self, status: str | None = None, ready: bool = False) -> list[AgentTaskSchema]:
        with SessionLocal() as session:
            query = session.query(AgentTaskRecord)
            if status:
                query = query.filter(AgentTaskRecord.status == status)
            records = query.order_by(AgentTaskRecord.created_at.desc()).all()
            tasks = [self._to_schema(record) for record in records]
            if ready:
                tasks = [
                    task for task in tasks
                    if task.status == "pending" and not task.blocked_by
                ]
            return tasks

    def get(self, task_id: str) -> AgentTaskSchema | None:
        with SessionLocal() as session:
            record = self._get_record(session, task_id)
            return self._to_schema(record) if record else None

    def update(self, task_id: str, request: TaskUpdateRequest) -> AgentTaskSchema | None:
        with SessionLocal() as session:
            record = self._get_record(session, task_id)
            if record is None:
                return None

            if request.subject is not None:
                record.subject = request.subject
            if request.description is not None:
                record.description = request.description
            if request.blocked_by is not None:
                record.blocked_by = request.blocked_by
                if record.status == "pending" and request.blocked_by:
                    record.status = "blocked"
                if record.status == "blocked" and not request.blocked_by:
                    record.status = "pending"
            if request.owner is not None:
                record.owner = request.owner
            if request.linked_case_id is not None:
                record.linked_case_id = request.linked_case_id
            if request.linked_run_id is not None:
                record.linked_run_id = request.linked_run_id
            if request.metadata is not None:
                record.metadata_payload = request.metadata
            if request.status is not None:
                record.status = request.status
                if request.status == "completed":
                    self._clear_dependency(session, task_id)
            record.updated_at = datetime.now(UTC).replace(tzinfo=None)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def mark_status(self, task_id: str, status: str, linked_run_id: str | None = None) -> None:
        with SessionLocal() as session:
            record = self._get_record(session, task_id)
            if record is None:
                return
            record.status = status
            if linked_run_id:
                record.linked_run_id = linked_run_id
            record.updated_at = datetime.now(UTC).replace(tzinfo=None)
            if status == "completed":
                self._clear_dependency(session, task_id)
            session.commit()

    def _get_record(self, session: Session, task_id: str) -> AgentTaskRecord | None:
        return (
            session.query(AgentTaskRecord)
            .filter(AgentTaskRecord.task_id == task_id)
            .one_or_none()
        )

    def _clear_dependency(self, session: Session, completed_task_id: str) -> None:
        records = session.query(AgentTaskRecord).all()
        for record in records:
            blocked_by = list(record.blocked_by or [])
            if completed_task_id not in blocked_by:
                continue
            blocked_by.remove(completed_task_id)
            record.blocked_by = blocked_by
            if record.status == "blocked" and not blocked_by:
                record.status = "pending"
            record.updated_at = datetime.now(UTC).replace(tzinfo=None)

    def _to_schema(self, record: AgentTaskRecord) -> AgentTaskSchema:
        return AgentTaskSchema(
            task_id=record.task_id,
            subject=record.subject,
            description=record.description,
            status=record.status,
            blocked_by=list(record.blocked_by or []),
            owner=record.owner,
            linked_case_id=record.linked_case_id,
            linked_run_id=record.linked_run_id,
            metadata=dict(record.metadata_payload or {}),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
