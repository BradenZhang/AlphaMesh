from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc

from app.db.init_db import init_db
from app.db.models import LLMCallRecord
from app.db.session import SessionLocal
from app.schemas.agents import LLMCallRecordSchema
from app.services.llm.pricing import estimate_cost_usd


class LLMCallLogger:
    def record(
        self,
        call_type: str,
        provider: str,
        model: str,
        usage: dict[str, int] | None = None,
        symbol: str | None = None,
        metadata: dict[str, object] | None = None,
        latency_ms: int = 0,
    ) -> str:
        init_db()
        normalized_usage = self.normalize_usage(usage)
        call_id = f"llm-{uuid4().hex}"
        with SessionLocal() as session:
            record = LLMCallRecord(
                call_id=call_id,
                call_type=call_type,
                symbol=symbol,
                provider=provider,
                model=model,
                prompt_tokens=normalized_usage["prompt_tokens"],
                completion_tokens=normalized_usage["completion_tokens"],
                total_tokens=normalized_usage["total_tokens"],
                metadata_payload=metadata,
                latency_ms=latency_ms,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            session.add(record)
            session.commit()
        return call_id

    def list_recent(self, limit: int = 20) -> list[LLMCallRecordSchema]:
        init_db()
        normalized_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            records = (
                session.query(LLMCallRecord)
                .order_by(desc(LLMCallRecord.created_at))
                .limit(normalized_limit)
                .all()
            )
            return [
                LLMCallRecordSchema(
                    call_id=record.call_id,
                    call_type=record.call_type,
                    symbol=record.symbol,
                    provider=record.provider,
                    model=record.model,
                    prompt_tokens=record.prompt_tokens,
                    completion_tokens=record.completion_tokens,
                    total_tokens=record.total_tokens,
                    metadata=record.metadata_payload,
                    latency_ms=record.latency_ms,
                    estimated_cost_usd=estimate_cost_usd(
                        record.provider,
                        record.model,
                        record.prompt_tokens,
                        record.completion_tokens,
                    ),
                    created_at=record.created_at,
                )
                for record in records
            ]

    def cost_by_task_type(self, limit: int = 200) -> dict[str, float]:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(LLMCallRecord)
                .order_by(desc(LLMCallRecord.created_at))
                .limit(limit)
                .all()
            )
            result: dict[str, float] = {}
            for record in records:
                cost = estimate_cost_usd(
                    record.provider,
                    record.model,
                    record.prompt_tokens,
                    record.completion_tokens,
                )
                task_type = record.call_type
                result[task_type] = result.get(task_type, 0.0) + cost
            return {k: round(v, 6) for k, v in result.items()}

    def normalize_usage(self, usage: dict[str, int] | None) -> dict[str, int]:
        usage = usage or {}
        prompt_tokens = int(
            usage.get("prompt_tokens")
            or usage.get("input_tokens")
            or usage.get("prompt")
            or 0
        )
        completion_tokens = int(
            usage.get("completion_tokens")
            or usage.get("output_tokens")
            or usage.get("completion")
            or 0
        )
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        return {
            "prompt_tokens": max(prompt_tokens, 0),
            "completion_tokens": max(completion_tokens, 0),
            "total_tokens": max(total_tokens, 0),
        }
