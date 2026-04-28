from pydantic import BaseModel, Field


class ResearchAnalyzeRequest(BaseModel):
    symbol: str


class ResearchReport(BaseModel):
    symbol: str
    summary: str
    key_metrics: dict[str, float | str]
    valuation_view: str
    risks: list[str]
    confidence_score: float = Field(ge=0, le=1)
