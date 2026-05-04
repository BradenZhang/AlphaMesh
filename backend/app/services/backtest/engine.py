from statistics import mean

from app.domain.enums import SignalAction, StrategyName
from app.schemas.backtest import BacktestResult, EquityPoint
from app.schemas.market import KlineBar
from app.services.backtest.base import BacktestRunner
from app.services.backtest.bias_guard import check_look_ahead_bias
from app.services.backtest.costs import apply_slippage, deduct_commission
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
        slippage_bps: float = 0.0,
        commission_per_trade: float = 0.0,
        walk_forward: bool = False,
        train_ratio: float = 0.7,
    ) -> BacktestResult:
        check_look_ahead_bias(bars, strategy_name.value)

        if walk_forward and len(bars) >= 20:
            return self._run_walk_forward(
                symbol, bars, strategy_name, initial_cash,
                slippage_bps, commission_per_trade, train_ratio,
            )
        return self._run_single(
            symbol, bars, strategy_name, initial_cash,
            slippage_bps, commission_per_trade,
        )

    def _run_single(
        self,
        symbol: str,
        bars: list[KlineBar],
        strategy_name: StrategyName,
        initial_cash: float,
        slippage_bps: float = 0.0,
        commission_per_trade: float = 0.0,
    ) -> BacktestResult:
        if len(bars) < 2:
            curve = [EquityPoint(timestamp="n/a", equity=initial_cash)]
            return self._build_result(
                symbol, strategy_name, curve, 0, 0, 0,
                slippage_bps, commission_per_trade,
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
                buy_price = apply_slippage(bar.close, "BUY", slippage_bps)
                allocation = cash * 0.5
                cash = deduct_commission(cash, commission_per_trade)
                shares = allocation / buy_price
                cash -= allocation
                entry_price = buy_price
                trade_count += 1
            elif action == SignalAction.SELL and shares > 0:
                sell_price = apply_slippage(bar.close, "SELL", slippage_bps)
                cash = deduct_commission(cash, commission_per_trade)
                cash += shares * sell_price
                closed_trades += 1
                wins += int(sell_price > entry_price)
                shares = 0.0
                trade_count += 1

            equity = cash + shares * bar.close
            equity_curve.append(
                EquityPoint(timestamp=bar.timestamp.isoformat(), equity=round(equity, 2))
            )

        if shares > 0:
            closed_trades += 1
            wins += int(bars[-1].close > entry_price)

        return self._build_result(
            symbol, strategy_name, equity_curve, wins, closed_trades, trade_count,
            slippage_bps, commission_per_trade,
        )

    def _run_walk_forward(
        self,
        symbol: str,
        bars: list[KlineBar],
        strategy_name: StrategyName,
        initial_cash: float,
        slippage_bps: float,
        commission_per_trade: float,
        train_ratio: float,
    ) -> BacktestResult:
        split_index = int(len(bars) * train_ratio)
        train_bars = bars[:split_index]
        test_bars = bars[split_index:]

        is_result = self._run_single(
            symbol, train_bars, strategy_name, initial_cash,
            slippage_bps, commission_per_trade,
        )
        oos_result = self._run_single(
            symbol, test_bars, strategy_name, initial_cash,
            slippage_bps, commission_per_trade,
        )

        badge = self._compute_validation_badge(is_result, oos_result)

        return BacktestResult(
            symbol=symbol.upper(),
            strategy_name=strategy_name,
            total_return=is_result.total_return,
            max_drawdown=is_result.max_drawdown,
            win_rate=is_result.win_rate,
            sharpe_ratio=is_result.sharpe_ratio,
            trade_count=is_result.trade_count,
            equity_curve=is_result.equity_curve,
            slippage_bps=slippage_bps,
            commission_per_trade=commission_per_trade,
            is_total_return=is_result.total_return,
            is_max_drawdown=is_result.max_drawdown,
            is_sharpe_ratio=is_result.sharpe_ratio,
            oos_total_return=oos_result.total_return,
            oos_max_drawdown=oos_result.max_drawdown,
            oos_sharpe_ratio=oos_result.sharpe_ratio,
            validation_badge=badge,
            look_ahead_bias_check=True,
        )

    def _compute_validation_badge(
        self, is_result: BacktestResult, oos_result: BacktestResult
    ) -> str:
        is_sharpe = is_result.sharpe_ratio
        oos_sharpe = oos_result.sharpe_ratio
        is_dd = is_result.max_drawdown
        oos_dd = oos_result.max_drawdown

        if is_sharpe <= 0:
            return "F"

        ratio = oos_sharpe / is_sharpe if is_sharpe else 0
        dd_ratio = oos_dd / is_dd if is_dd else 0

        if ratio >= 0.8 and dd_ratio <= 1.5:
            return "A"
        if ratio >= 0.6 and dd_ratio <= 2.0:
            return "B"
        if ratio >= 0.4:
            return "C"
        if ratio >= 0.2:
            return "D"
        return "F"

    def _build_result(
        self,
        symbol: str,
        strategy_name: StrategyName,
        equity_curve: list[EquityPoint],
        wins: int,
        closed_trades: int,
        trade_count: int,
        slippage_bps: float = 0.0,
        commission_per_trade: float = 0.0,
    ) -> BacktestResult:
        return BacktestResult(
            symbol=symbol.upper(),
            strategy_name=strategy_name,
            total_return=calculate_total_return(equity_curve),
            max_drawdown=calculate_max_drawdown(equity_curve),
            win_rate=wins / closed_trades if closed_trades else 0.0,
            sharpe_ratio=calculate_sharpe_ratio(equity_curve),
            trade_count=trade_count,
            equity_curve=equity_curve,
            slippage_bps=slippage_bps,
            commission_per_trade=commission_per_trade,
            look_ahead_bias_check=True,
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
