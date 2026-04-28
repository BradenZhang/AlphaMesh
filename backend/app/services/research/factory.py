from app.core.config import Settings, get_settings
from app.services.agents.runtime import AgentRuntime
from app.services.llm.factory import get_llm_provider, get_llm_provider_for_profile
from app.services.research.base import ResearchAgent
from app.services.research.llm_agent import LLMResearchAgent
from app.services.research.mock_agent import MockResearchAgent


def get_research_agent(
    settings: Settings | None = None,
    llm_profile_id: str | None = None,
) -> ResearchAgent:
    settings = settings or get_settings()
    if settings.llm_provider.lower() == "legacy_mock" and not llm_profile_id:
        return MockResearchAgent()
    provider = (
        get_llm_provider_for_profile(llm_profile_id, settings)
        if llm_profile_id
        else get_llm_provider(settings)
    )
    return LLMResearchAgent(runtime=AgentRuntime(llm_provider=provider))
