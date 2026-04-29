from fastapi import APIRouter, HTTPException, status

from app.api.deps import validate_symbol
from app.schemas.research import ResearchAnalyzeRequest, ResearchReport
from app.services.research.factory import get_research_agent

router = APIRouter()


@router.post("/analyze", response_model=ResearchReport)
def analyze(request: ResearchAnalyzeRequest) -> ResearchReport:
    validated = validate_symbol(request.symbol)
    try:
        return get_research_agent(llm_profile_id=request.llm_profile_id).analyze(validated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
