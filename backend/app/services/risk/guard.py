from app.core.config import Settings, get_settings
from app.domain.enums import AutomationMode, RiskLevel, SignalAction
from app.schemas.risk import RiskCheckRequest, RiskResult
from app.services.risk.base import RiskGuardBase


class RiskGuard(RiskGuardBase):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def check(self, request: RiskCheckRequest) -> RiskResult:
        reasons: list[str] = []
        risk_level = RiskLevel.LOW

        projected_position = request.current_position_pct + request.signal.suggested_position_pct
        if projected_position > self.settings.single_symbol_max_position_pct:
            reasons.append("Single-symbol position limit exceeded.")
            risk_level = RiskLevel.HIGH

        if (
            request.order_request is not None
            and request.order_request.estimated_amount > self.settings.max_order_amount
        ):
            reasons.append("Single-order amount limit exceeded.")
            risk_level = RiskLevel.HIGH

        if (
            request.backtest_result is not None
            and request.backtest_result.max_drawdown > self.settings.max_drawdown_threshold
        ):
            reasons.append("Backtest max drawdown exceeds configured threshold.")
            risk_level = RiskLevel.HIGH

        if request.signal.confidence < 0.5:
            reasons.append("Signal confidence is below minimum review threshold.")
            if risk_level != RiskLevel.HIGH:
                risk_level = RiskLevel.MEDIUM

        if request.signal.action == SignalAction.HOLD:
            reasons.append("Signal action is HOLD, no execution is recommended.")

        if risk_level == RiskLevel.HIGH and request.mode != AutomationMode.MANUAL:
            reasons.append("Automatic execution is blocked when risk level is HIGH.")

        approved = risk_level != RiskLevel.HIGH
        if request.mode != AutomationMode.MANUAL and request.signal.action == SignalAction.HOLD:
            approved = False

        if not reasons:
            reasons.append("Risk checks passed under MVP mock rules.")

        return RiskResult(approved=approved, risk_level=risk_level, reasons=reasons)
