from pydantic import BaseModel, Field


class ResearchAnalyzeRequest(BaseModel):
    symbol: str
    llm_profile_id: str | None = None
    market_provider: str | None = None


class ResearchReport(BaseModel):
    symbol: str
    summary: str
    key_metrics: dict[str, float | str]
    valuation_view: str
    risks: list[str]
    confidence_score: float = Field(ge=0, le=1)
    data_sources: list[str] = Field(default_factory=list)
