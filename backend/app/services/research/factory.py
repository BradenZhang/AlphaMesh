from app.core.config import Settings, get_settings
from app.services.agents.runtime import AgentRuntime
from app.services.llm.factory import get_llm_provider
from app.services.research.base import ResearchAgent
from app.services.research.llm_agent import LLMResearchAgent
from app.services.research.mock_agent import MockResearchAgent


def get_research_agent(settings: Settings | None = None) -> ResearchAgent:
    settings = settings or get_settings()
    if settings.llm_provider.lower() == "legacy_mock":
        return MockResearchAgent()
    return LLMResearchAgent(runtime=AgentRuntime(llm_provider=get_llm_provider(settings)))
