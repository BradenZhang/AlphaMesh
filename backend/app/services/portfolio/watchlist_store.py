from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc

from app.db.init_db import init_db
from app.db.models import WatchlistItemRecord
from app.db.session import SessionLocal
from app.schemas.portfolio import WatchlistItemCreate, WatchlistItemSchema


class WatchlistStore:
    def add(self, item: WatchlistItemCreate, user_id: str = "default") -> WatchlistItemSchema:
        init_db()
        symbol = item.symbol.upper()
        with SessionLocal() as session:
            existing = (
                session.query(WatchlistItemRecord)
                .filter(
                    WatchlistItemRecord.user_id == user_id,
                    WatchlistItemRecord.symbol == symbol,
                )
                .first()
            )
            if existing is not None:
                raise ValueError(f"{symbol} is already in the watchlist.")

            record = WatchlistItemRecord(
                item_id=f"wl-{uuid4().hex}",
                symbol=symbol,
                label=item.label,
                sector=item.sector,
                industry=item.industry,
                user_id=user_id,
                added_at=datetime.now(UTC).replace(tzinfo=None),
                notes=item.notes,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def remove(self, item_id: str, user_id: str = "default") -> bool:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(WatchlistItemRecord)
                .filter(
                    WatchlistItemRecord.item_id == item_id,
                    WatchlistItemRecord.user_id == user_id,
                )
                .first()
            )
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True

    def list_items(self, user_id: str = "default") -> list[WatchlistItemSchema]:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(WatchlistItemRecord)
                .filter(WatchlistItemRecord.user_id == user_id)
                .order_by(desc(WatchlistItemRecord.added_at))
                .all()
            )
            return [self._to_schema(r) for r in records]

    def get_by_symbol(self, symbol: str, user_id: str = "default") -> WatchlistItemSchema | None:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(WatchlistItemRecord)
                .filter(
                    WatchlistItemRecord.user_id == user_id,
                    WatchlistItemRecord.symbol == symbol.upper(),
                )
                .first()
            )
            return self._to_schema(record) if record else None

    def has_symbol(self, symbol: str, user_id: str = "default") -> bool:
        return self.get_by_symbol(symbol, user_id) is not None

    def _to_schema(self, record: WatchlistItemRecord) -> WatchlistItemSchema:
        return WatchlistItemSchema(
            item_id=record.item_id,
            symbol=record.symbol,
            label=record.label,
            sector=record.sector,
            industry=record.industry,
            user_id=record.user_id,
            added_at=record.added_at,
            notes=record.notes,
        )
