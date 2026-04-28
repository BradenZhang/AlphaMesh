from app.domain.enums import AutomationMode, OrderSide, RiskLevel, SignalAction, StrategyName
from app.schemas.order import OrderRequest
from app.schemas.risk import RiskCheckRequest
from app.schemas.strategy import StrategySignal
from app.services.risk.guard import RiskGuard


def test_risk_guard_blocks_oversized_order_and_position() -> None:
    signal = StrategySignal(
        symbol="AAPL",
        action=SignalAction.BUY,
        confidence=0.8,
        reason="test",
        suggested_position_pct=0.5,
        stop_loss=90,
        take_profit=120,
        strategy_name=StrategyName.MOVING_AVERAGE_CROSS,
    )
    order = OrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1_000,
        limit_price=150,
        estimated_amount=150_000,
    )

    result = RiskGuard().check(
        RiskCheckRequest(
            signal=signal,
            order_request=order,
            mode=AutomationMode.PAPER_AUTO,
        )
    )

    assert result.approved is False
    assert result.risk_level == RiskLevel.HIGH
    assert any("limit" in reason.lower() for reason in result.reasons)
