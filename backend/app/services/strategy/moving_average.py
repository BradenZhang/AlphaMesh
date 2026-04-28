from statistics import mean

from app.domain.enums import SignalAction, StrategyName
from app.schemas.market import FundamentalsResponse, KlineBar
from app.schemas.research import ResearchReport
from app.schemas.strategy import StrategySignal
from app.services.strategy.base import Strategy


class MovingAverageCrossStrategy(Strategy):
    short_window = 5
    long_window = 20

    def generate_signal(
        self,
        symbol: str,
        bars: list[KlineBar] | None = None,
        fundamentals: FundamentalsResponse | None = None,
        research_report: ResearchReport | None = None,
    ) -> StrategySignal:
        if not bars or len(bars) < self.long_window:
            return StrategySignal(
                symbol=symbol.upper(),
                action=SignalAction.HOLD,
                confidence=0.35,
                reason="Not enough bars for moving average crossover.",
                suggested_position_pct=0.0,
                stop_loss=None,
                take_profit=None,
                strategy_name=StrategyName.MOVING_AVERAGE_CROSS,
            )

        closes = [bar.close for bar in bars]
        short_ma = mean(closes[-self.short_window :])
        long_ma = mean(closes[-self.long_window :])
        latest = closes[-1]

        if short_ma > long_ma * 1.005:
            action = SignalAction.BUY
            position = 0.18
            reason = f"Short MA {short_ma:.2f} is above long MA {long_ma:.2f}."
        elif short_ma < long_ma * 0.995:
            action = SignalAction.SELL
            position = 0.0
            reason = f"Short MA {short_ma:.2f} is below long MA {long_ma:.2f}."
        else:
            action = SignalAction.HOLD
            position = 0.0
            reason = f"Short MA {short_ma:.2f} is close to long MA {long_ma:.2f}."

        confidence = min(0.9, 0.55 + abs(short_ma - long_ma) / max(long_ma, 1))
        return StrategySignal(
            symbol=symbol.upper(),
            action=action,
            confidence=confidence,
            reason=reason,
            suggested_position_pct=position,
            stop_loss=round(latest * 0.92, 2) if action == SignalAction.BUY else None,
            take_profit=round(latest * 1.18, 2) if action == SignalAction.BUY else None,
            strategy_name=StrategyName.MOVING_AVERAGE_CROSS,
        )
