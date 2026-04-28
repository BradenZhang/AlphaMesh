from dataclasses import dataclass


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    max_drawdown: float
    win_rate: float
    sharpe_ratio: float
    trade_count: int
