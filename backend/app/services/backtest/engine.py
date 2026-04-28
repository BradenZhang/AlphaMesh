from statistics import mean

from app.domain.enums import SignalAction, StrategyName
from app.schemas.backtest import BacktestResult, EquityPoint
from app.schemas.market import KlineBar
from app.services.backtest.base import BacktestRunner
from app.services.backtest.metrics import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
)


class BacktestEngine(BacktestRunner):
    def run(
        self,
        symbol: str,
        bars: list[KlineBar],
        strategy_name: StrategyName = StrategyName.MOVING_AVERAGE_CROSS,
        initial_cash: float = 100_000.0,
    ) -> BacktestResult:
        if len(bars) < 2:
            curve = [EquityPoint(timestamp="n/a", equity=initial_cash)]
            return BacktestResult(
                symbol=symbol.upper(),
                strategy_name=strategy_name,
                total_return=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                sharpe_ratio=0.0,
                trade_count=0,
                equity_curve=curve,
            )

        cash = initial_cash
        shares = 0.0
        entry_price = 0.0
        wins = 0
        closed_trades = 0
        trade_count = 0
        equity_curve: list[EquityPoint] = []

        for index, bar in enumerate(bars):
            action = self._signal_for_bar(bars[: index + 1], strategy_name)
            if action == SignalAction.BUY and shares == 0:
                allocation = cash * 0.5
                shares = allocation / bar.close
                cash -= allocation
                entry_price = bar.close
                trade_count += 1
            elif action == SignalAction.SELL and shares > 0:
                cash += shares * bar.close
                closed_trades += 1
                wins += int(bar.close > entry_price)
                shares = 0.0
                trade_count += 1

            equity = cash + shares * bar.close
            equity_curve.append(
                EquityPoint(timestamp=bar.timestamp.isoformat(), equity=round(equity, 2))
            )

        if shares > 0:
            closed_trades += 1
            wins += int(bars[-1].close > entry_price)

        return BacktestResult(
            symbol=symbol.upper(),
            strategy_name=strategy_name,
            total_return=calculate_total_return(equity_curve),
            max_drawdown=calculate_max_drawdown(equity_curve),
            win_rate=wins / closed_trades if closed_trades else 0.0,
            sharpe_ratio=calculate_sharpe_ratio(equity_curve),
            trade_count=trade_count,
            equity_curve=equity_curve,
        )

    def _signal_for_bar(self, bars: list[KlineBar], strategy_name: StrategyName) -> SignalAction:
        if strategy_name == StrategyName.VALUATION_BAND:
            return SignalAction.BUY if bars[-1].close < 95 else SignalAction.HOLD
        if len(bars) < 20:
            return SignalAction.HOLD
        closes = [bar.close for bar in bars]
        short_ma = mean(closes[-5:])
        long_ma = mean(closes[-20:])
        if short_ma > long_ma * 1.003:
            return SignalAction.BUY
        if short_ma < long_ma * 0.997:
            return SignalAction.SELL
        return SignalAction.HOLD
