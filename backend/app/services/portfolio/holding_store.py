from datetime import UTC, datetime
from uuid import uuid4

from app.db.init_db import init_db
from app.db.models import PortfolioHoldingRecord
from app.db.session import SessionLocal
from app.schemas.order import OrderResponse
from app.schemas.portfolio import PortfolioHoldingSchema


class PortfolioHoldingStore:
    def upsert_from_order(
        self,
        order: OrderResponse,
        sector: str | None = None,
        industry: str | None = None,
    ) -> PortfolioHoldingSchema | None:
        init_db()
        symbol = order.symbol.upper()
        price = order.limit_price or 0.0
        now = datetime.now(UTC).replace(tzinfo=None)

        with SessionLocal() as session:
            record = (
                session.query(PortfolioHoldingRecord)
                .filter(
                    PortfolioHoldingRecord.symbol == symbol,
                    PortfolioHoldingRecord.user_id == "default",
                )
                .first()
            )

            if order.side.value.upper() == "SELL":
                if record is None:
                    return None
                record.quantity = max(0.0, record.quantity - order.quantity)
                record.last_updated = now
                if record.quantity <= 0:
                    session.delete(record)
                    session.commit()
                    return None
                session.commit()
                session.refresh(record)
                return self._to_schema(record)

            # BUY logic
            if record is None:
                record = PortfolioHoldingRecord(
                    holding_id=f"hold-{uuid4().hex}",
                    symbol=symbol,
                    quantity=order.quantity,
                    avg_cost=price,
                    current_price=price,
                    sector=sector,
                    industry=industry,
                    user_id="default",
                    last_updated=now,
                    source="paper_order",
                )
                session.add(record)
            else:
                total_cost = record.avg_cost * record.quantity + price * order.quantity
                record.quantity += order.quantity
                record.avg_cost = total_cost / record.quantity if record.quantity else 0.0
                record.current_price = price
                record.last_updated = now

            session.commit()
            session.refresh(record)
            return self._to_schema(record)

    def list_holdings(self, user_id: str = "default") -> list[PortfolioHoldingSchema]:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(PortfolioHoldingRecord)
                .filter(PortfolioHoldingRecord.user_id == user_id)
                .all()
            )
            return [self._to_schema(r) for r in records]

    def get_holding(self, symbol: str, user_id: str = "default") -> PortfolioHoldingSchema | None:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(PortfolioHoldingRecord)
                .filter(
                    PortfolioHoldingRecord.symbol == symbol.upper(),
                    PortfolioHoldingRecord.user_id == user_id,
                )
                .first()
            )
            return self._to_schema(record) if record else None

    def update_prices(self, prices: dict[str, float]) -> None:
        init_db()
        with SessionLocal() as session:
            records = (
                session.query(PortfolioHoldingRecord)
                .filter(PortfolioHoldingRecord.symbol.in_(list(prices.keys())))
                .all()
            )
            for record in records:
                if record.symbol in prices:
                    record.current_price = prices[record.symbol]
                    record.last_updated = datetime.now(UTC).replace(tzinfo=None)
            session.commit()

    def delete_holding(self, symbol: str, user_id: str = "default") -> bool:
        init_db()
        with SessionLocal() as session:
            record = (
                session.query(PortfolioHoldingRecord)
                .filter(
                    PortfolioHoldingRecord.symbol == symbol.upper(),
                    PortfolioHoldingRecord.user_id == user_id,
                )
                .first()
            )
            if record is None:
                return False
            session.delete(record)
            session.commit()
            return True

    def _to_schema(self, record: PortfolioHoldingRecord) -> PortfolioHoldingSchema:
        market_value = record.quantity * record.current_price
        cost_basis = record.quantity * record.avg_cost
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_pct = unrealized_pnl / cost_basis if cost_basis else 0.0
        return PortfolioHoldingSchema(
            holding_id=record.holding_id,
            symbol=record.symbol,
            quantity=record.quantity,
            avg_cost=record.avg_cost,
            current_price=record.current_price,
            market_value=round(market_value, 2),
            unrealized_pnl=round(unrealized_pnl, 2),
            unrealized_pnl_pct=round(unrealized_pnl_pct, 4),
            sector=record.sector,
            industry=record.industry,
            weight=0.0,
        )
