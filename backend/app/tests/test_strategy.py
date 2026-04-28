from app.domain.enums import SignalAction
from app.services.market.mock_provider import MockSkillProvider
from app.services.strategy.moving_average import MovingAverageCrossStrategy
from app.services.strategy.valuation_band import ValuationBandStrategy


def test_moving_average_strategy_generates_signal() -> None:
    provider = MockSkillProvider()
    bars = provider.get_kline("AAPL").bars

    signal = MovingAverageCrossStrategy().generate_signal("AAPL", bars=bars)

    assert signal.symbol == "AAPL"
    assert signal.action in {SignalAction.BUY, SignalAction.SELL, SignalAction.HOLD}
    assert 0 <= signal.confidence <= 1
    assert signal.reason


def test_valuation_band_strategy_uses_fundamentals() -> None:
    provider = MockSkillProvider()
    fundamentals = provider.get_fundamentals("AAPL")

    signal = ValuationBandStrategy().generate_signal("AAPL", fundamentals=fundamentals)

    assert signal.symbol == "AAPL"
    assert signal.action == SignalAction.HOLD
    assert "neutral" in signal.reason.lower()
