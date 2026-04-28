from datetime import datetime

from pydantic import BaseModel


class AgentRunRecordSchema(BaseModel):
    run_id: str
    run_type: str
    status: str
    symbol: str | None = None
    provider: str | None = None
    model: str | None = None
    input_payload: dict | None = None
    output_payload: dict | None = None
    error_message: str | None = None
    latency_ms: int
    created_at: datetime


class AgentRunListResponse(BaseModel):
    runs: list[AgentRunRecordSchema]
