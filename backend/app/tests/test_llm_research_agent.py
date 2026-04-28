from app.services.agents.runtime import AgentRuntime
from app.services.agents.tool_registry import ToolRegistry
from app.services.llm.providers.mock_provider import MockLLMProvider
from app.services.market.mock_provider import MockSkillProvider
from app.services.research.llm_agent import LLMResearchAgent


def test_llm_research_agent_returns_valid_report() -> None:
    runtime = AgentRuntime(
        llm_provider=MockLLMProvider(),
        tool_registry=ToolRegistry(market_provider=MockSkillProvider()),
    )

    report = LLMResearchAgent(runtime=runtime).analyze("AAPL")

    assert report.symbol == "AAPL"
    assert report.summary
    assert report.key_metrics["llm_provider"] == "mock"
    assert report.risks
    assert 0 <= report.confidence_score <= 1
