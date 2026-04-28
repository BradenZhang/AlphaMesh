import json
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.schemas.agents import (
    AgentFinding,
    InvestmentCommitteeReport,
    RiskReviewReport,
    StrategyReviewReport,
)
from app.schemas.backtest import BacktestResult
from app.schemas.research import ResearchReport
from app.schemas.risk import RiskResult
from app.schemas.strategy import StrategySignal
from app.services.agents.base import AgentRuntimeBase
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.tool_registry import ToolRegistry
from app.services.llm.base import LLMProvider
from app.services.llm.call_logger import LLMCallLogger
from app.services.llm.factory import get_llm_provider
from app.services.llm.output_guard import LLMOutputGuard
from app.services.llm.schemas import LLMMessage, LLMResponse
from app.services.memory.store import MemoryStore

ModelT = TypeVar("ModelT", bound=BaseModel)


class AgentRuntime(AgentRuntimeBase):
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
        output_guard: LLMOutputGuard | None = None,
        run_logger: AgentRunLogger | None = None,
        llm_call_logger: LLMCallLogger | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or ToolRegistry()
        self.output_guard = output_guard or LLMOutputGuard()
        self.run_logger = run_logger or AgentRunLogger()
        self.llm_call_logger = llm_call_logger or LLMCallLogger()
        self.memory_store = memory_store or MemoryStore()

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
            self._record_llm_usage(
                call_type="research",
                symbol=normalized,
                response=response,
                latency_ms=self._elapsed_ms(started_at),
            )
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

    def run_json_agent(
        self,
        agent_name: str,
        symbol: str,
        system_prompt: str,
        user_payload: dict[str, object],
        response_model: type[ModelT],
        fallback_payload: dict[str, object],
    ) -> ModelT:
        normalized = symbol.upper()
        provider_info = self.llm_provider.get_provider_info()
        started_at = time.perf_counter()
        memory_context = self._get_memory_context(normalized)
        user_payload_with_memory = {
            **user_payload,
            "memory_context": memory_context,
        }
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {"symbol": normalized, **user_payload_with_memory},
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        ]
        input_payload = {"messages": [message.model_dump() for message in messages]}

        try:
            response = self.llm_provider.generate(messages=messages, temperature=0.2)
            self._record_llm_usage(
                call_type=agent_name,
                symbol=normalized,
                response=response,
                latency_ms=self._elapsed_ms(started_at),
            )
            parsed = self.output_guard._extract_json(response.content)
            result = response_model.model_validate(parsed)
            self.run_logger.record(
                run_type=agent_name,
                status="success",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload=input_payload,
                output_payload=result.model_dump(mode="json"),
                latency_ms=self._elapsed_ms(started_at),
            )
            self._remember_agent_result(agent_name, normalized, result.model_dump(mode="json"))
            return result
        except (ValueError, ValidationError) as exc:
            fallback_payload = {"symbol": normalized, **fallback_payload}
            result = response_model.model_validate(fallback_payload)
            self.run_logger.record(
                run_type=agent_name,
                status="fallback",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload={
                    **input_payload,
                    "fallback_reason": str(exc),
                },
                output_payload=result.model_dump(mode="json"),
                latency_ms=self._elapsed_ms(started_at),
            )
            self._remember_agent_result(
                agent_name,
                normalized,
                result.model_dump(mode="json"),
                fallback_reason=str(exc),
            )
            return result

    def run_financial_statement_agent(self, symbol: str) -> AgentFinding:
        normalized = symbol.upper()
        context = self.tool_registry.get_market_context(normalized)
        return self.run_json_agent(
            agent_name="financial_statement_agent",
            symbol=normalized,
            system_prompt=(
                "You are a financial statement analyst. Return JSON matching AgentFinding."
            ),
            user_payload={"market_context": context},
            response_model=AgentFinding,
            fallback_payload={
                "agent_name": "Financial Statement Agent",
                "thesis": f"{normalized} shows stable profitability and mock revenue resilience.",
                "key_points": [
                    "Revenue growth remains positive in mock fundamentals.",
                    "Net margin suggests durable operating efficiency.",
                    "Leverage is controlled under the demo assumptions.",
                ],
                "metrics": {
                    "revenue_growth": 0.16,
                    "net_margin": 0.21,
                    "debt_to_equity": 0.38,
                },
                "risks": ["Financial data is mock and not a real filing analysis."],
                "confidence_score": 0.74,
            },
        )

    def run_valuation_agent(self, symbol: str) -> AgentFinding:
        normalized = symbol.upper()
        context = self.tool_registry.get_market_context(normalized)
        return self.run_json_agent(
            agent_name="valuation_agent",
            symbol=normalized,
            system_prompt="You are a valuation analyst. Return JSON matching AgentFinding.",
            user_payload={"market_context": context},
            response_model=AgentFinding,
            fallback_payload={
                "agent_name": "Valuation Agent",
                "thesis": f"{normalized} valuation is reasonable relative to mock growth.",
                "key_points": [
                    "PE ratio is inside the neutral demo band.",
                    "PB ratio does not indicate extreme valuation pressure.",
                    "Growth supports a balanced HOLD to selective BUY bias.",
                ],
                "metrics": {"pe_ratio": 18.5, "pb_ratio": 2.1},
                "risks": ["Valuation bands are simplified for MVP demonstration."],
                "confidence_score": 0.68,
            },
        )

    def run_industry_agent(self, symbol: str) -> AgentFinding:
        normalized = symbol.upper()
        return self.run_json_agent(
            agent_name="industry_agent",
            symbol=normalized,
            system_prompt="You are an industry analyst. Return JSON matching AgentFinding.",
            user_payload={"scope": "mock industry context"},
            response_model=AgentFinding,
            fallback_payload={
                "agent_name": "Industry Agent",
                "thesis": f"{normalized} benefits from resilient sector demand in mock context.",
                "key_points": [
                    "Industry demand is assumed stable in the demo.",
                    "Competitive position is treated as neutral to positive.",
                    "Macro sensitivity remains a monitoring item.",
                ],
                "metrics": {"industry_momentum": "neutral_positive"},
                "risks": ["No real industry data feed is connected in this MVP."],
                "confidence_score": 0.64,
            },
        )

    def run_news_agent(self, symbol: str) -> AgentFinding:
        normalized = symbol.upper()
        return self.run_json_agent(
            agent_name="news_agent",
            symbol=normalized,
            system_prompt=(
                "You are a news and sentiment analyst. Return JSON matching AgentFinding."
            ),
            user_payload={"scope": "mock news context"},
            response_model=AgentFinding,
            fallback_payload={
                "agent_name": "News Agent",
                "thesis": f"{normalized} has no severe negative mock news catalyst.",
                "key_points": [
                    "No high-impact negative headline is present in mock data.",
                    "Sentiment is treated as balanced for demonstration.",
                    "Real-time news integration is not enabled.",
                ],
                "metrics": {"news_sentiment": "neutral"},
                "risks": ["Mock news cannot reflect breaking market events."],
                "confidence_score": 0.6,
            },
        )

    def run_investment_committee(
        self,
        symbol: str,
        findings: list[AgentFinding],
    ) -> InvestmentCommitteeReport:
        normalized = symbol.upper()
        average_confidence = sum(f.confidence_score for f in findings) / max(len(findings), 1)
        fallback = {
            "summary": (
                f"{normalized} receives a balanced multi-agent view with supportive "
                "fundamentals, reasonable valuation, and no severe mock news risk."
            ),
            "consensus_view": "Constructive but still requires human review before any real use.",
            "key_debates": [finding.thesis for finding in findings],
            "action_bias": "BUY" if average_confidence >= 0.68 else "HOLD",
            "confidence_score": min(0.82, max(0.45, average_confidence)),
        }
        return self.run_json_agent(
            agent_name="investment_committee_agent",
            symbol=normalized,
            system_prompt=(
                "You are an investment committee. Synthesize findings into "
                "InvestmentCommitteeReport JSON."
            ),
            user_payload={"findings": [finding.model_dump(mode="json") for finding in findings]},
            response_model=InvestmentCommitteeReport,
            fallback_payload=fallback,
        )

    def run_strategy_review(
        self,
        symbol: str,
        research: ResearchReport,
        signal: StrategySignal,
        backtest: BacktestResult,
    ) -> StrategyReviewReport:
        normalized = symbol.upper()
        aligned = signal.confidence >= 0.5 and backtest.max_drawdown <= 0.2
        return self.run_json_agent(
            agent_name="strategy_review_agent",
            symbol=normalized,
            system_prompt="You are a strategy review agent. Return StrategyReviewReport JSON.",
            user_payload={
                "research": research.model_dump(mode="json"),
                "signal": signal.model_dump(mode="json"),
                "backtest": backtest.model_dump(mode="json"),
            },
            response_model=StrategyReviewReport,
            fallback_payload={
                "aligned": aligned,
                "review_summary": (
                    f"Strategy signal {signal.action} is "
                    f"{'aligned' if aligned else 'not fully aligned'} "
                    "with mock research and backtest constraints."
                ),
                "strengths": [signal.reason, f"Backtest win rate {backtest.win_rate:.2%}."],
                "concerns": (
                    ["Drawdown needs attention."]
                    if backtest.max_drawdown > 0.2
                    else ["Result is based on mock data only."]
                ),
                "confidence_score": min(0.8, max(0.45, signal.confidence)),
            },
        )

    def run_risk_review(
        self,
        symbol: str,
        signal: StrategySignal,
        risk_result: RiskResult,
    ) -> RiskReviewReport:
        normalized = symbol.upper()
        approved_for_auto = risk_result.approved and risk_result.risk_level != "HIGH"
        return self.run_json_agent(
            agent_name="risk_review_agent",
            symbol=normalized,
            system_prompt="You are a risk review agent. Return RiskReviewReport JSON.",
            user_payload={
                "signal": signal.model_dump(mode="json"),
                "risk_result": risk_result.model_dump(mode="json"),
            },
            response_model=RiskReviewReport,
            fallback_payload={
                "approved_for_auto": approved_for_auto,
                "review_summary": (
                    "Risk review agrees with automatic paper execution."
                    if approved_for_auto
                    else "Risk review does not recommend automatic execution."
                ),
                "risk_flags": risk_result.reasons,
                "confidence_score": 0.72 if approved_for_auto else 0.58,
            },
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    def _record_llm_usage(
        self,
        call_type: str,
        symbol: str,
        response: LLMResponse,
        latency_ms: int,
    ) -> None:
        self.llm_call_logger.record(
            call_type=call_type,
            symbol=symbol,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            latency_ms=latency_ms,
        )

    def _get_memory_context(self, symbol: str) -> dict[str, object]:
        context = self.memory_store.search_context(symbol=symbol, limit=10, token_budget=700)
        return context.model_dump(mode="json")

    def _remember_agent_result(
        self,
        agent_name: str,
        symbol: str,
        payload: dict[str, object],
        fallback_reason: str | None = None,
    ) -> None:
        content = self._extract_memory_content(agent_name, payload)
        metadata = {"agent_name": agent_name, "source": "agent_runtime"}
        if fallback_reason:
            metadata["fallback_reason"] = fallback_reason

        scope = "long_term" if agent_name == "investment_committee_agent" else "short_term"
        memory_type = "risk_note" if agent_name == "risk_review_agent" else "research_summary"
        ttl_seconds = None if scope == "long_term" else 86_400
        self.memory_store.write(
            request=self.memory_store_write_request(
                scope=scope,
                memory_type=memory_type,
                symbol=symbol,
                content=content,
                metadata=metadata,
                importance_score=0.78 if scope == "long_term" else 0.5,
                ttl_seconds=ttl_seconds,
            )
        )

    def memory_store_write_request(
        self,
        scope: str,
        memory_type: str,
        symbol: str,
        content: str,
        metadata: dict[str, object],
        importance_score: float,
        ttl_seconds: int | None,
    ):
        from app.schemas.memory import MemoryWriteRequest

        return MemoryWriteRequest(
            scope=scope,
            memory_type=memory_type,
            symbol=symbol,
            content=content,
            metadata=metadata,
            importance_score=importance_score,
            ttl_seconds=ttl_seconds,
        )

    def _extract_memory_content(self, agent_name: str, payload: dict[str, object]) -> str:
        for key in ("summary", "thesis", "review_summary", "consensus_view"):
            value = payload.get(key)
            if value:
                return f"{agent_name}: {value}"
        return f"{agent_name}: {json.dumps(payload, ensure_ascii=False, default=str)[:300]}"
