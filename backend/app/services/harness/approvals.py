from datetime import UTC, datetime
from uuid import uuid4

from app.db.init_db import init_db
from app.db.models import ApprovalRequestRecord
from app.db.session import SessionLocal
from app.schemas.harness import (
    ApprovalCreateRequest,
    ApprovalRequestSchema,
    ApprovalRespondRequest,
)


class ApprovalStore:
    def __init__(self) -> None:
        init_db()

    def create(self, request: ApprovalCreateRequest) -> ApprovalRequestSchema:
        with SessionLocal() as session:
            record = ApprovalRequestRecord(
                approval_id=f"approval-{uuid4().hex}",
                request_type=request.request_type,
                status="pending",
                subject=request.subject,
                requested_by=request.requested_by,
                target=request.target,
                linked_task_id=request.linked_task_id,
                linked_run_id=request.linked_run_id,
                payload=request.payload,
                response_payload={},
                expires_at=request.expires_at.replace(tzinfo=None)
                if request.expires_at else None,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def list(self, status: str | None = None) -> list[ApprovalRequestSchema]:
        self.expire_due()
        with SessionLocal() as session:
            query = session.query(ApprovalRequestRecord)
            if status:
                query = query.filter(ApprovalRequestRecord.status == status)
            records = query.order_by(ApprovalRequestRecord.created_at.desc()).all()
            return [self._to_schema(record) for record in records]

    def get(self, approval_id: str) -> ApprovalRequestSchema | None:
        self.expire_due()
        with SessionLocal() as session:
            record = self._get_record(session, approval_id)
            return self._to_schema(record) if record else None

    def respond(
        self,
        approval_id: str,
        request: ApprovalRespondRequest,
    ) -> ApprovalRequestSchema | None:
        self.expire_due()
        with SessionLocal() as session:
            record = self._get_record(session, approval_id)
            if record is None:
                return None
            if record.status != "pending":
                raise ValueError(f"Approval '{approval_id}' is already {record.status}.")
            record.status = "approved" if request.approve else "rejected"
            record.reason = request.reason
            record.response_payload = request.response
            record.decided_at = datetime.now(UTC).replace(tzinfo=None)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def expire_due(self) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        with SessionLocal() as session:
            records = (
                session.query(ApprovalRequestRecord)
                .filter(ApprovalRequestRecord.status == "pending")
                .filter(ApprovalRequestRecord.expires_at.isnot(None))
                .filter(ApprovalRequestRecord.expires_at <= now)
                .all()
            )
            for record in records:
                record.status = "expired"
                record.decided_at = now
                record.reason = "Approval request expired."
            if records:
                session.commit()

    def _get_record(self, session, approval_id: str) -> ApprovalRequestRecord | None:
        return (
            session.query(ApprovalRequestRecord)
            .filter(ApprovalRequestRecord.approval_id == approval_id)
            .one_or_none()
        )

    def _to_schema(self, record: ApprovalRequestRecord) -> ApprovalRequestSchema:
        return ApprovalRequestSchema(
            approval_id=record.approval_id,
            request_type=record.request_type,
            status=record.status,
            subject=record.subject,
            requested_by=record.requested_by,
            target=record.target,
            linked_task_id=record.linked_task_id,
            linked_run_id=record.linked_run_id,
            payload=dict(record.payload or {}),
            response=dict(record.response_payload or {}),
            reason=record.reason,
            expires_at=record.expires_at,
            decided_at=record.decided_at,
            created_at=record.created_at,
        )
