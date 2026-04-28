from app.services.backtest.engine import BacktestEngine
from app.services.market.mock_provider import MockSkillProvider


def test_backtest_metrics_calculation() -> None:
    provider = MockSkillProvider()
    bars = provider.get_kline("AAPL").bars

    result = BacktestEngine().run("AAPL", bars)

    assert result.symbol == "AAPL"
    assert len(result.equity_curve) == len(bars)
    assert result.trade_count >= 0
    assert -1 < result.total_return < 1
    assert 0 <= result.max_drawdown <= 1
    assert 0 <= result.win_rate <= 1
