from fastapi import APIRouter

from app.schemas.research import ResearchAnalyzeRequest, ResearchReport
from app.services.research.factory import get_research_agent

router = APIRouter()


@router.post("/analyze", response_model=ResearchReport)
def analyze(request: ResearchAnalyzeRequest) -> ResearchReport:
    return get_research_agent().analyze(request.symbol)
