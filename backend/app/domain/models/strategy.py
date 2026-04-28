from dataclasses import dataclass

from app.domain.enums import SignalAction


@dataclass(frozen=True)
class StrategySignalModel:
    symbol: str
    action: SignalAction
    confidence: float
    reason: str
    suggested_position_pct: float
