import math
from statistics import mean, pstdev

from app.schemas.backtest import EquityPoint


def calculate_total_return(equity_curve: list[EquityPoint]) -> float:
    if len(equity_curve) < 2:
        return 0.0
    start = equity_curve[0].equity
    end = equity_curve[-1].equity
    return (end - start) / start if start else 0.0


def calculate_max_drawdown(equity_curve: list[EquityPoint]) -> float:
    peak = -math.inf
    max_drawdown = 0.0
    for point in equity_curve:
        peak = max(peak, point.equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - point.equity) / peak)
    return max_drawdown


def calculate_sharpe_ratio(equity_curve: list[EquityPoint]) -> float:
    if len(equity_curve) < 3:
        return 0.0
    returns = [
        (equity_curve[index].equity - equity_curve[index - 1].equity)
        / equity_curve[index - 1].equity
        for index in range(1, len(equity_curve))
        if equity_curve[index - 1].equity
    ]
    if len(returns) < 2:
        return 0.0
    volatility = pstdev(returns)
    if volatility == 0:
        return 0.0
    return mean(returns) / volatility * math.sqrt(252)
