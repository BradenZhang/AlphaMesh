from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc

from app.db.init_db import init_db
from app.db.models import InvestmentCaseRecord
from app.db.session import SessionLocal
from app.schemas.case import InvestmentCaseSchema


class InvestmentCaseStore:
    def create(
        self,
        symbol: str,
        thesis: str,
        confidence: float,
        risks: list[str],
        data_sources: list[str],
        decision: str,
        order_id: str | None = None,
        run_id: str | None = None,
        conversation_id: str | None = None,
    ) -> InvestmentCaseSchema:
        init_db()
        now = datetime.now(UTC).replace(tzinfo=None)
        case_id = f"case-{uuid4().hex}"
        with SessionLocal() as session:
            record = InvestmentCaseRecord(
                case_id=case_id,
                symbol=symbol.upper(),
                thesis=thesis,
                confidence=confidence,
                risks=risks,
                data_sources=data_sources,
                decision=decision.lower(),
                order_id=order_id,
                run_id=run_id,
                conversation_id=conversation_id,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def list_recent(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[InvestmentCaseSchema]:
        init_db()
        normalized_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            query = session.query(InvestmentCaseRecord)
            if symbol:
                query = query.filter(InvestmentCaseRecord.symbol == symbol.upper())
            records = (
                query.order_by(desc(InvestmentCaseRecord.created_at))
                .limit(normalized_limit)
                .all()
            )
            return [self._to_schema(record) for record in records]

    def get(self, case_id: str) -> InvestmentCaseSchema:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(InvestmentCaseRecord)
                .filter(InvestmentCaseRecord.case_id == case_id)
                .first()
            )
            if record is None:
                raise ValueError(f"Investment case '{case_id}' not found.")
            return self._to_schema(record)

    def update_outcome(self, case_id: str, outcome: str) -> InvestmentCaseSchema:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(InvestmentCaseRecord)
                .filter(InvestmentCaseRecord.case_id == case_id)
                .first()
            )
            if record is None:
                raise ValueError(f"Investment case '{case_id}' not found.")
            record.outcome = outcome
            record.updated_at = datetime.now(UTC).replace(tzinfo=None)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def _to_schema(self, record: InvestmentCaseRecord) -> InvestmentCaseSchema:
        return InvestmentCaseSchema(
            case_id=record.case_id,
            symbol=record.symbol,
            thesis=record.thesis,
            confidence=record.confidence,
            risks=record.risks or [],
            data_sources=record.data_sources or [],
            decision=record.decision,
            order_id=record.order_id,
            outcome=record.outcome,
            run_id=record.run_id,
            conversation_id=record.conversation_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
