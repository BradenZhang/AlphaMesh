from datetime import datetime

from pydantic import BaseModel


class InvestmentCaseSchema(BaseModel):
    case_id: str
    symbol: str
    thesis: str
    confidence: float
    risks: list[str]
    data_sources: list[str]
    decision: str
    order_id: str | None = None
    outcome: str | None = None
    run_id: str | None = None
    conversation_id: str | None = None
    created_at: datetime
    updated_at: datetime


class InvestmentCaseListResponse(BaseModel):
    cases: list[InvestmentCaseSchema]


class InvestmentCaseUpdateRequest(BaseModel):
    outcome: str | None = None
