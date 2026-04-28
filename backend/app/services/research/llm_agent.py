from app.schemas.research import ResearchReport
from app.services.agents.base import AgentRuntimeBase
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.runtime import AgentRuntime
from app.services.llm.output_guard import LLMOutputValidationError
from app.services.research.base import ResearchAgent
from app.services.research.mock_agent import MockResearchAgent


class LLMResearchAgent(ResearchAgent):
    def __init__(
        self,
        runtime: AgentRuntimeBase | None = None,
        run_logger: AgentRunLogger | None = None,
    ) -> None:
        self.runtime = runtime or AgentRuntime()
        self.fallback_agent = MockResearchAgent()
        self.run_logger = run_logger or AgentRunLogger()

    def analyze(self, symbol: str) -> ResearchReport:
        try:
            return self.runtime.run_research(symbol)
        except LLMOutputValidationError as exc:
            report = self.fallback_agent.analyze(symbol)
            report.key_metrics["llm_fallback"] = "output_validation_failed"
            self.run_logger.record(
                run_type="research_fallback",
                status="success",
                symbol=symbol.upper(),
                provider="mock",
                model="mock-research-v1",
                input_payload={"symbol": symbol.upper(), "fallback_reason": str(exc)},
                output_payload=report.model_dump(mode="json"),
            )
            return report
