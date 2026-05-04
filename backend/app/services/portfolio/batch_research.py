from app.schemas.agents import MultiAgentResearchReport
from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.runtime import AgentRuntime


class BatchResearchService:
    def __init__(
        self,
        runtime: AgentRuntime | None = None,
    ) -> None:
        self.runtime = runtime or AgentRuntime()

    def run_all(
        self,
        symbols: list[str],
    ) -> dict[str, MultiAgentResearchReport]:
        workflow = MultiAgentResearchWorkflow(runtime=self.runtime)
        results: dict[str, MultiAgentResearchReport] = {}
        for symbol in symbols:
            try:
                results[symbol.upper()] = workflow.run(symbol)
            except Exception:
                continue
        return results
