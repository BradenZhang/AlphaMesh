from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.runtime import AgentRuntime
from app.services.llm.base import LLMProvider
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse
from app.services.research.llm_agent import LLMResearchAgent


class InvalidJSONProvider(LLMProvider):
    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        return LLMResponse(content="not json", provider="broken", model="broken")

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="broken", model="broken", is_mock=True)


def test_llm_research_agent_falls_back_on_invalid_output() -> None:
    agent = LLMResearchAgent(runtime=AgentRuntime(llm_provider=InvalidJSONProvider()))

    report = agent.analyze("AAPL")

    assert report.symbol == "AAPL"
    assert report.key_metrics["agent_count"] == 4
    assert report.summary
    runs = AgentRunLogger().list_recent(limit=10)
    assert any(
        run.run_type == "financial_statement_agent"
        and run.status == "fallback"
        and run.symbol == "AAPL"
        for run in runs
    )
