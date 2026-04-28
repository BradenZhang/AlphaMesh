from app.domain.enums import SignalAction, StrategyName
from app.schemas.market import FundamentalsResponse, KlineBar
from app.schemas.research import ResearchReport
from app.schemas.strategy import StrategySignal
from app.services.strategy.base import Strategy


class ValuationBandStrategy(Strategy):
    def generate_signal(
        self,
        symbol: str,
        bars: list[KlineBar] | None = None,
        fundamentals: FundamentalsResponse | None = None,
        research_report: ResearchReport | None = None,
    ) -> StrategySignal:
        if fundamentals is None:
            return StrategySignal(
                symbol=symbol.upper(),
                action=SignalAction.HOLD,
                confidence=0.35,
                reason="Fundamentals are required for valuation band strategy.",
                suggested_position_pct=0.0,
                stop_loss=None,
                take_profit=None,
                strategy_name=StrategyName.VALUATION_BAND,
            )

        latest_close = bars[-1].close if bars else 100.0
        if fundamentals.pe_ratio < 15 and fundamentals.revenue_growth > 0.08:
            action = SignalAction.BUY
            reason = "PE is below the lower valuation band while growth remains positive."
            position = 0.16
        elif fundamentals.pe_ratio > 35 or fundamentals.debt_to_equity > 1.2:
            action = SignalAction.SELL
            reason = "Valuation or leverage exceeds the upper risk band."
            position = 0.0
        else:
            action = SignalAction.HOLD
            reason = "Valuation sits inside the neutral band."
            position = 0.0

        return StrategySignal(
            symbol=symbol.upper(),
            action=action,
            confidence=0.68 if action != SignalAction.HOLD else 0.52,
            reason=reason,
            suggested_position_pct=position,
            stop_loss=round(latest_close * 0.9, 2) if action == SignalAction.BUY else None,
            take_profit=round(latest_close * 1.22, 2) if action == SignalAction.BUY else None,
            strategy_name=StrategyName.VALUATION_BAND,
        )
