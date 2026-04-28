import json
import time

from app.schemas.research import ResearchReport
from app.services.agents.base import AgentRuntimeBase
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.tool_registry import ToolRegistry
from app.services.llm.base import LLMProvider
from app.services.llm.factory import get_llm_provider
from app.services.llm.output_guard import LLMOutputGuard
from app.services.llm.schemas import LLMMessage


class AgentRuntime(AgentRuntimeBase):
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
        output_guard: LLMOutputGuard | None = None,
        run_logger: AgentRunLogger | None = None,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or ToolRegistry()
        self.output_guard = output_guard or LLMOutputGuard()
        self.run_logger = run_logger or AgentRunLogger()

    def run_research(self, symbol: str) -> ResearchReport:
        normalized = symbol.upper()
        context = self.tool_registry.get_market_context(normalized)
        provider_info = self.llm_provider.get_provider_info()
        started_at = time.perf_counter()
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are an equity research agent. Return JSON only with keys: "
                    "symbol, summary, key_metrics, valuation_view, risks, confidence_score."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"symbol: {normalized}\n"
                    f"market_context: {json.dumps(context, ensure_ascii=False)}"
                ),
            ),
        ]

        try:
            response = self.llm_provider.generate(messages=messages, temperature=0.2)
            report = self.output_guard.parse_research_report(response.content, normalized)
            self.run_logger.record(
                run_type="research",
                status="success",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload={
                    "messages": [message.model_dump() for message in messages],
                    "market_context": context,
                },
                output_payload=report.model_dump(mode="json"),
                latency_ms=self._elapsed_ms(started_at),
            )
            return report
        except Exception as exc:
            self.run_logger.record(
                run_type="research",
                status="failed",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload={
                    "messages": [message.model_dump() for message in messages],
                    "market_context": context,
                },
                error_message=str(exc),
                latency_ms=self._elapsed_ms(started_at),
            )
            raise

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)
