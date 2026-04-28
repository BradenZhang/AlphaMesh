import json
import time

from app.schemas.agents import (
    ReActObservation,
    ReActRunResponse,
    ReActStep,
    ReActToolCall,
)
from app.schemas.memory import MemoryWriteRequest
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.tool_registry import ToolRegistry
from app.services.llm.base import LLMProvider
from app.services.llm.call_logger import LLMCallLogger
from app.services.llm.factory import get_llm_provider
from app.services.llm.output_guard import LLMOutputGuard, LLMOutputValidationError
from app.services.llm.schemas import LLMMessage
from app.services.memory.store import MemoryStore


class ReActRuntime:
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        tool_registry: ToolRegistry | None = None,
        run_logger: AgentRunLogger | None = None,
        llm_call_logger: LLMCallLogger | None = None,
        memory_store: MemoryStore | None = None,
    ) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.tool_registry = tool_registry or ToolRegistry()
        self.run_logger = run_logger or AgentRunLogger()
        self.llm_call_logger = llm_call_logger or LLMCallLogger()
        self.output_guard = LLMOutputGuard()
        self.memory_store = memory_store or MemoryStore()

    def run(
        self,
        symbol: str,
        question: str | None = None,
        llm_profile_id: str | None = None,
        max_steps: int = 3,
    ) -> ReActRunResponse:
        normalized = symbol.upper()
        started_at = time.perf_counter()
        provider_info = self.llm_provider.get_provider_info()
        memory_context = self.memory_store.search_context(
            symbol=normalized,
            limit=10,
            token_budget=700,
        )

        try:
            response = (
                self._run_deterministic_trace(
                    normalized,
                    question,
                    llm_profile_id,
                    max_steps,
                    memory_context.context,
                )
                if provider_info.is_mock
                else self._run_llm_trace(
                    normalized,
                    question,
                    llm_profile_id,
                    max_steps,
                    memory_context.context,
                )
            )
            self.run_logger.record(
                run_type="react_agent",
                status="success",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload={
                    "symbol": normalized,
                    "question": question,
                    "llm_profile_id": llm_profile_id,
                    "max_steps": max_steps,
                },
                output_payload=response.model_dump(mode="json"),
                latency_ms=self._elapsed_ms(started_at),
            )
            self._remember_trace(response)
            return response
        except (ValueError, LLMOutputValidationError) as exc:
            response = self._run_deterministic_trace(
                normalized,
                question,
                llm_profile_id,
                max_steps,
                memory_context.context,
                fallback_reason=str(exc),
            )
            self.run_logger.record(
                run_type="react_agent",
                status="fallback",
                symbol=normalized,
                provider=provider_info.provider,
                model=provider_info.model,
                input_payload={
                    "symbol": normalized,
                    "question": question,
                    "llm_profile_id": llm_profile_id,
                    "max_steps": max_steps,
                    "fallback_reason": str(exc),
                },
                output_payload=response.model_dump(mode="json"),
                latency_ms=self._elapsed_ms(started_at),
            )
            self._remember_trace(response, fallback_reason=str(exc))
            return response

    def _run_llm_trace(
        self,
        symbol: str,
        question: str | None,
        llm_profile_id: str | None,
        max_steps: int,
        memory_context: str,
    ) -> ReActRunResponse:
        steps: list[ReActStep] = []
        transcript: list[dict[str, object]] = []

        for step_number in range(1, max_steps + 1):
            messages = self._build_action_messages(
                symbol,
                question,
                transcript,
                step_number,
                memory_context,
            )
            started_at = time.perf_counter()
            llm_response = self.llm_provider.generate(messages=messages, temperature=0.1)
            self.llm_call_logger.record(
                call_type="react_agent_action",
                symbol=symbol,
                provider=llm_response.provider,
                model=llm_response.model,
                usage=llm_response.usage,
                latency_ms=self._elapsed_ms(started_at),
                metadata={"step_number": step_number},
            )
            action_payload = self.output_guard._extract_json(llm_response.content)

            if action_payload.get("final_answer"):
                return ReActRunResponse(
                    symbol=symbol,
                    llm_profile_id=llm_profile_id,
                    steps=steps,
                    final_answer=str(action_payload["final_answer"]),
                    confidence_score=float(action_payload.get("confidence_score", 0.65)),
                )

            tool_call = ReActToolCall(
                tool_name=str(action_payload.get("action") or ""),
                arguments=dict(action_payload.get("action_input") or {"symbol": symbol}),
            )
            observation = ReActObservation.model_validate(
                self.tool_registry.run_tool(tool_call.tool_name, tool_call.arguments)
            )
            step = ReActStep(
                step_number=step_number,
                rationale_summary=str(
                    action_payload.get("rationale_summary")
                    or "Agent selected a read-only tool based on the research question."
                ),
                tool_call=tool_call,
                observation=observation,
            )
            steps.append(step)
            transcript.append(step.model_dump(mode="json"))

        return ReActRunResponse(
            symbol=symbol,
            llm_profile_id=llm_profile_id,
            steps=steps,
            final_answer=self._summarize_trace(symbol, steps, question),
            confidence_score=0.68,
        )

    def _run_deterministic_trace(
        self,
        symbol: str,
        question: str | None,
        llm_profile_id: str | None,
        max_steps: int,
        memory_context: str,
        fallback_reason: str | None = None,
    ) -> ReActRunResponse:
        planned_tools = [
            (
                "get_quote",
                "先查看价格、涨跌幅和成交量，建立行情基线。",
                {"symbol": symbol},
            ),
            (
                "get_fundamentals",
                "再读取估值和财务指标，判断基本面质量。",
                {"symbol": symbol},
            ),
            (
                "get_kline",
                "最后读取近期 K 线，观察趋势和样本数量。",
                {"symbol": symbol, "interval": "1d"},
            ),
        ][:max_steps]
        steps = [
            self._build_step(index + 1, tool_name, rationale, arguments)
            for index, (tool_name, rationale, arguments) in enumerate(planned_tools)
        ]
        final_answer = self._summarize_trace(symbol, steps, question)
        if fallback_reason:
            final_answer = f"{final_answer} ReAct fallback reason: {fallback_reason}"
        if memory_context and memory_context != "No prior memory context is available.":
            final_answer = f"{final_answer} Memory context was considered."
        return ReActRunResponse(
            symbol=symbol,
            llm_profile_id=llm_profile_id,
            steps=steps,
            final_answer=final_answer,
            confidence_score=0.72,
        )

    def _build_step(
        self,
        step_number: int,
        tool_name: str,
        rationale_summary: str,
        arguments: dict[str, object],
    ) -> ReActStep:
        tool_call = ReActToolCall(tool_name=tool_name, arguments=arguments)
        observation = ReActObservation.model_validate(
            self.tool_registry.run_tool(tool_name, arguments)
        )
        return ReActStep(
            step_number=step_number,
            rationale_summary=rationale_summary,
            tool_call=tool_call,
            observation=observation,
        )

    def _build_action_messages(
        self,
        symbol: str,
        question: str | None,
        transcript: list[dict[str, object]],
        step_number: int,
        memory_context: str,
    ) -> list[LLMMessage]:
        allowed_tools = "get_quote, get_kline, get_fundamentals, get_market_context"
        return [
            LLMMessage(
                role="system",
                content=(
                    "You are a ReAct-lite investment research agent. "
                    "Do not reveal chain-of-thought. Return JSON only. "
                    "Choose one read-only action or return final_answer. "
                    f"Allowed actions: {allowed_tools}. "
                    "Action JSON keys: action, action_input, rationale_summary. "
                    "Final JSON keys: final_answer, confidence_score."
                ),
            ),
            LLMMessage(
                role="user",
                content=json.dumps(
                    {
                        "symbol": symbol,
                        "question": question
                        or "Use read-only tools to form a concise research view.",
                        "step_number": step_number,
                        "previous_steps": transcript,
                        "memory_context": memory_context,
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        ]

    def _summarize_trace(
        self,
        symbol: str,
        steps: list[ReActStep],
        question: str | None,
    ) -> str:
        successful = [step for step in steps if step.observation.success]
        tool_names = ", ".join(step.tool_call.tool_name for step in successful)
        prompt = question or "形成投研辅助结论"
        return (
            f"{symbol} ReAct-lite completed {len(successful)} read-only tool checks "
            f"({tool_names}) for: {prompt}. Results are for engineering demo only "
            "and are not investment advice."
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    def _remember_trace(
        self,
        response: ReActRunResponse,
        fallback_reason: str | None = None,
    ) -> None:
        metadata: dict[str, object] = {
            "source": "react_runtime",
            "step_count": len(response.steps),
            "tools": [step.tool_call.tool_name for step in response.steps],
        }
        if fallback_reason:
            metadata["fallback_reason"] = fallback_reason
        self.memory_store.write(
            MemoryWriteRequest(
                scope="short_term",
                memory_type="react_trace",
                symbol=response.symbol,
                content=response.final_answer,
                metadata=metadata,
                importance_score=0.56,
                ttl_seconds=86_400,
            )
        )
