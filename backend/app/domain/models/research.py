from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchReportModel:
    symbol: str
    summary: str
    valuation_view: str
    risks: list[str]
    confidence_score: float
