from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc

from app.db.init_db import init_db
from app.db.models import AgentRunRecord
from app.db.session import SessionLocal
from app.schemas.agents import AgentRunRecordSchema


class AgentRunLogger:
    def record(
        self,
        run_type: str,
        status: str,
        symbol: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        input_payload: dict | None = None,
        output_payload: dict | None = None,
        error_message: str | None = None,
        latency_ms: int = 0,
        run_id: str | None = None,
        market_provider: str | None = None,
        execution_provider: str | None = None,
        account_provider: str | None = None,
    ) -> str:
        init_db()
        run_id = run_id or f"run-{uuid4().hex}"
        with SessionLocal() as session:
            record = AgentRunRecord(
                run_id=run_id,
                run_type=run_type,
                status=status,
                symbol=symbol,
                provider=provider,
                model=model,
                input_payload=input_payload,
                output_payload=output_payload,
                error_message=error_message,
                latency_ms=latency_ms,
                market_provider=market_provider,
                execution_provider=execution_provider,
                account_provider=account_provider,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add(record)
            session.commit()
        return run_id

    def list_recent(self, limit: int = 20) -> list[AgentRunRecordSchema]:
        init_db()
        normalized_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            records = (
                session.query(AgentRunRecord)
                .order_by(desc(AgentRunRecord.created_at))
                .limit(normalized_limit)
                .all()
            )
            return [
                AgentRunRecordSchema(
                    run_id=record.run_id,
                    run_type=record.run_type,
                    status=record.status,
                    symbol=record.symbol,
                    provider=record.provider,
                    model=record.model,
                    input_payload=record.input_payload,
                    output_payload=record.output_payload,
                    error_message=record.error_message,
                    latency_ms=record.latency_ms,
                    created_at=record.created_at,
                    market_provider=record.market_provider,
                    execution_provider=record.execution_provider,
                    account_provider=record.account_provider,
                )
                for record in records
            ]

    def get_by_run_id(self, run_id: str) -> AgentRunRecordSchema | None:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(AgentRunRecord)
                .filter(AgentRunRecord.run_id == run_id)
                .first()
            )
            if record is None:
                return None
            return AgentRunRecordSchema(
                run_id=record.run_id,
                run_type=record.run_type,
                status=record.status,
                symbol=record.symbol,
                provider=record.provider,
                model=record.model,
                input_payload=record.input_payload,
                output_payload=record.output_payload,
                error_message=record.error_message,
                latency_ms=record.latency_ms,
                created_at=record.created_at,
                market_provider=record.market_provider,
                execution_provider=record.execution_provider,
                account_provider=record.account_provider,
            )
