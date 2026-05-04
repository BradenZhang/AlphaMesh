from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.models import AgentPlanRecord
from app.db.session import SessionLocal
from app.schemas.harness import AgentPlanSchema, PlanStepSchema, PlanUpdateRequest


class AgentPlanStore:
    def __init__(self) -> None:
        init_db()

    def update_plan(self, request: PlanUpdateRequest) -> AgentPlanSchema:
        in_progress = [step for step in request.steps if step.status == "in_progress"]
        if len(in_progress) > 1:
            raise ValueError("Only one plan step can be in_progress.")

        with SessionLocal() as session:
            plan_id = request.plan_id or f"plan-{uuid4().hex}"
            record = (
                session.query(AgentPlanRecord)
                .filter(AgentPlanRecord.plan_id == plan_id)
                .one_or_none()
            )
            now = datetime.now(UTC).replace(tzinfo=None)
            if record is None:
                record = AgentPlanRecord(
                    plan_id=plan_id,
                    owner_type=request.owner_type,
                    owner_id=request.owner_id,
                    symbol=request.symbol.upper() if request.symbol else None,
                    status="active",
                    steps_payload=[],
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)

            record.owner_type = request.owner_type
            record.owner_id = request.owner_id
            record.symbol = request.symbol.upper() if request.symbol else record.symbol
            record.steps_payload = [step.model_dump(mode="json") for step in request.steps]
            record.status = "completed" if all(
                step.status == "completed" for step in request.steps
            ) else "active"
            record.updated_at = now
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def get_plan(self, plan_id: str) -> AgentPlanSchema | None:
        with SessionLocal() as session:
            record = (
                session.query(AgentPlanRecord)
                .filter(AgentPlanRecord.plan_id == plan_id)
                .one_or_none()
            )
            return self._to_schema(record) if record else None

    def _to_schema(self, record: AgentPlanRecord) -> AgentPlanSchema:
        return AgentPlanSchema(
            plan_id=record.plan_id,
            owner_type=record.owner_type,
            owner_id=record.owner_id,
            symbol=record.symbol,
            status=record.status,
            steps=[
                PlanStepSchema.model_validate(step)
                for step in (record.steps_payload or [])
            ],
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def update_plan_in_session(
    session: Session,
    plan_id: str,
    steps: list[PlanStepSchema],
) -> AgentPlanSchema | None:
    record = session.query(AgentPlanRecord).filter(AgentPlanRecord.plan_id == plan_id).one_or_none()
    if record is None:
        return None
    record.steps_payload = [step.model_dump(mode="json") for step in steps]
    record.updated_at = datetime.now(UTC).replace(tzinfo=None)
    session.commit()
    session.refresh(record)
    return AgentPlanStore()._to_schema(record)
