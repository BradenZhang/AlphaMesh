from dataclasses import dataclass

from app.domain.enums import RiskLevel


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    risk_level: RiskLevel
    reasons: list[str]
