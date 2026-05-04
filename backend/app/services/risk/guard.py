from app.core.config import Settings, get_settings
from app.domain.enums import AutomationMode, RiskLevel, SignalAction
from app.schemas.portfolio import PortfolioSummary, RebalanceProposal, RebalanceRiskReview
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

    def check_rebalance(
        self,
        proposal: RebalanceProposal,
        portfolio_summary: PortfolioSummary,
    ) -> RebalanceRiskReview:
        reasons: list[str] = []
        risk_level = "LOW"
        flagged_orders: list[str] = []

        for order in proposal.orders:
            if order.estimated_amount > self.settings.max_order_amount:
                flagged_orders.append(order.symbol)
                reasons.append(
                    f"{order.symbol}: order amount ${order.estimated_amount:,.2f} "
                    f"exceeds limit ${self.settings.max_order_amount:,.2f}."
                )
                risk_level = "HIGH"

            if order.target_weight > self.settings.single_symbol_max_position_pct:
                flagged_orders.append(order.symbol)
                reasons.append(
                    f"{order.symbol}: target weight {order.target_weight:.2%} "
                    f"exceeds single-symbol max {self.settings.single_symbol_max_position_pct:.2%}."
                )
                risk_level = "HIGH"

        if proposal.estimated_turnover > 0.5:
            reasons.append(
                f"Turnover {proposal.estimated_turnover:.2%} is high (>50%)."
            )
            if risk_level != "HIGH":
                risk_level = "MEDIUM"

        if proposal.cash_after < 0:
            reasons.append("Rebalance would result in negative cash.")
            risk_level = "HIGH"
        elif portfolio_summary.total_portfolio_value > 0:
            cash_ratio = proposal.cash_after / portfolio_summary.total_portfolio_value
            if cash_ratio < 0.05:
                reasons.append(
                    f"Cash after rebalance ({cash_ratio:.2%}) is below 5% minimum."
                )
                if risk_level != "HIGH":
                    risk_level = "MEDIUM"

        if not reasons:
            reasons.append("Rebalance risk checks passed.")

        approved = risk_level != "HIGH"
        return RebalanceRiskReview(
            approved=approved,
            risk_level=risk_level,
            reasons=reasons,
            flagged_orders=list(set(flagged_orders)),
        )
