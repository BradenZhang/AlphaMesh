from sqlalchemy import desc

from app.db.init_db import init_db
from app.db.models import PaperOrderRecord
from app.db.session import SessionLocal
from app.domain.enums import OrderSide, OrderStatus
from app.schemas.order import OrderResponse, PaperOrderRecordResponse


class PaperOrderStore:
    def save(self, order: OrderResponse) -> None:
        init_db()
        with SessionLocal() as session:
            record = PaperOrderRecord(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                limit_price=order.limit_price,
                status=order.status.value,
                broker=order.broker,
                account_id=order.account_id,
                external_order_id=order.external_order_id,
                environment=order.environment,
                created_at=order.created_at.replace(tzinfo=None),
            )
            session.add(record)
            session.commit()

    def list_recent(self, limit: int = 20) -> list[PaperOrderRecordResponse]:
        init_db()
        normalized_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            records = (
                session.query(PaperOrderRecord)
                .order_by(desc(PaperOrderRecord.created_at))
                .limit(normalized_limit)
                .all()
            )
            return [self._to_schema(record) for record in records]

    def _to_schema(self, record: PaperOrderRecord) -> PaperOrderRecordResponse:
        estimated_amount = (
            round(record.quantity * record.limit_price, 2)
            if record.limit_price is not None
            else None
        )
        return PaperOrderRecordResponse(
            order_id=record.order_id,
            symbol=record.symbol,
            side=OrderSide(record.side),
            quantity=record.quantity,
            limit_price=record.limit_price,
            estimated_amount=estimated_amount,
            status=OrderStatus(record.status),
            created_at=record.created_at,
        )
