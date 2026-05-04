from datetime import UTC, datetime
from uuid import uuid4

from app.db.init_db import init_db
from app.db.models import RunCheckpointRecord
from app.db.session import SessionLocal
from app.schemas.automation import RunCheckpointSchema


class CheckpointStore:
    def save(
        self,
        run_id: str,
        step_id: str,
        step_label: str,
        status: str,
        input_snapshot: dict | None = None,
        output_snapshot: dict | None = None,
        error: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration_ms: int = 0,
    ) -> RunCheckpointSchema:
        init_db()
        with SessionLocal() as session:
            existing = (
                session.query(RunCheckpointRecord)
                .filter(
                    RunCheckpointRecord.run_id == run_id,
                    RunCheckpointRecord.step_id == step_id,
                )
                .first()
            )
            now = datetime.now(UTC).replace(tzinfo=None)
            if existing:
                existing.status = status
                if output_snapshot is not None:
                    existing.output_snapshot = output_snapshot
                if error is not None:
                    existing.error = error
                if completed_at is not None:
                    existing.completed_at = completed_at
                if duration_ms:
                    existing.duration_ms = duration_ms
                session.commit()
                session.refresh(existing)
                return self._to_schema(existing)

            record = RunCheckpointRecord(
                checkpoint_id=f"cp-{uuid4().hex}",
                run_id=run_id,
                step_id=step_id,
                step_label=step_label,
                status=status,
                input_snapshot=input_snapshot,
                output_snapshot=output_snapshot,
                error=error,
                started_at=started_at or now,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def get_completed_steps(self, run_id: str) -> dict[str, RunCheckpointRecord]:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(RunCheckpointRecord)
                .filter(
                    RunCheckpointRecord.run_id == run_id,
                    RunCheckpointRecord.status == "completed",
                )
                .all()
            )
            return {record.step_id: record for record in records}

    def get_all(self, run_id: str) -> list[RunCheckpointSchema]:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(RunCheckpointRecord)
                .filter(RunCheckpointRecord.run_id == run_id)
                .order_by(RunCheckpointRecord.id)
                .all()
            )
            return [self._to_schema(record) for record in records]

    def clear(self, run_id: str) -> None:
        init_db()
        with SessionLocal() as session:
            session.query(RunCheckpointRecord).filter(
                RunCheckpointRecord.run_id == run_id
            ).delete()
            session.commit()

    def _to_schema(self, record: RunCheckpointRecord) -> RunCheckpointSchema:
        return RunCheckpointSchema(
            checkpoint_id=record.checkpoint_id,
            run_id=record.run_id,
            step_id=record.step_id,
            step_label=record.step_label,
            status=record.status,
            input_snapshot=record.input_snapshot,
            output_snapshot=record.output_snapshot,
            error=record.error,
            started_at=record.started_at,
            completed_at=record.completed_at,
            duration_ms=record.duration_ms,
        )
