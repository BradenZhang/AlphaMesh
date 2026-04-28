from app.schemas.memory import MemoryRecordSchema
from app.services.llm.base import LLMProvider
from app.services.llm.call_logger import LLMCallLogger
from app.services.llm.factory import get_llm_provider
from app.services.llm.schemas import LLMMessage
from app.services.memory.token_budget import TokenBudgetManager


class ContextCompressor:
    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        token_budget: TokenBudgetManager | None = None,
        call_logger: LLMCallLogger | None = None,
        chunk_size: int = 5,
    ) -> None:
        self.llm_provider = llm_provider
        self.token_budget = token_budget or TokenBudgetManager()
        self.call_logger = call_logger or LLMCallLogger()
        self.chunk_size = chunk_size
        self.last_metadata: dict[str, object] = {}

    def compress(self, memories: list[MemoryRecordSchema], max_items: int = 8) -> str:
        if not memories:
            self.last_metadata = {
                "strategy": "none",
                "map_calls": 0,
                "reduce_calls": 0,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            return "No prior memory context is available."

        lines = []
        for memory in memories[:max_items]:
            symbol = f"[{memory.symbol}] " if memory.symbol else ""
            lines.append(
                f"- {symbol}{memory.scope}/{memory.memory_type}: "
                f"{self._shorten(memory.content)}"
            )
        self.last_metadata = {
            "strategy": "direct",
            "map_calls": 0,
            "reduce_calls": 0,
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
        return "\n".join(lines)

    def compress_map_reduce(
        self,
        memories: list[MemoryRecordSchema],
        symbol: str | None = None,
        max_summary_tokens: int | None = None,
    ) -> str:
        if not memories:
            return self.compress(memories)

        provider = self.llm_provider or get_llm_provider()
        provider_info = provider.get_provider_info()
        chunks = [
            memories[index : index + self.chunk_size]
            for index in range(0, len(memories), self.chunk_size)
        ]
        map_summaries: list[str] = []
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for index, chunk in enumerate(chunks, start=1):
            messages = self._build_map_messages(chunk, index, symbol, max_summary_tokens)
            response = provider.generate(messages=messages, temperature=0.1)
            usage = self.call_logger.normalize_usage(response.usage)
            self._merge_usage(token_usage, usage)
            self.call_logger.record(
                call_type="memory_map_summary",
                symbol=symbol,
                provider=provider_info.provider,
                model=provider_info.model,
                usage=usage,
                metadata={"chunk_index": index, "chunk_size": len(chunk)},
            )
            map_summaries.append(response.content.strip() or self._fallback_summary(chunk))

        if len(map_summaries) == 1:
            self.last_metadata = {
                "strategy": "map_reduce",
                "map_calls": 1,
                "reduce_calls": 0,
                "chunk_count": 1,
                "token_usage": token_usage,
            }
            return map_summaries[0]

        reduce_messages = self._build_reduce_messages(map_summaries, symbol, max_summary_tokens)
        reduce_response = provider.generate(messages=reduce_messages, temperature=0.1)
        usage = self.call_logger.normalize_usage(reduce_response.usage)
        self._merge_usage(token_usage, usage)
        self.call_logger.record(
            call_type="memory_reduce_summary",
            symbol=symbol,
            provider=provider_info.provider,
            model=provider_info.model,
            usage=usage,
            metadata={"summary_count": len(map_summaries)},
        )
        self.last_metadata = {
            "strategy": "map_reduce",
            "map_calls": len(map_summaries),
            "reduce_calls": 1,
            "chunk_count": len(chunks),
            "token_usage": token_usage,
        }
        return reduce_response.content.strip() or "\n".join(map_summaries)

    def _shorten(self, text: str, limit: int = 220) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return f"{normalized[: limit - 3]}..."

    def _build_map_messages(
        self,
        memories: list[MemoryRecordSchema],
        chunk_index: int,
        symbol: str | None,
        max_summary_tokens: int | None,
    ) -> list[LLMMessage]:
        return [
            LLMMessage(
                role="system",
                content=(
                    "You are a memory summarizer. Summarize this chunk of old "
                    "investment research messages. Keep durable preferences, key "
                    "facts, risks, and decisions. Return concise plain text only."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"symbol: {symbol or 'GLOBAL'}\n"
                    f"chunk_index: {chunk_index}\n"
                    f"max_summary_tokens: {max_summary_tokens or 180}\n"
                    f"messages:\n{self._format_memories(memories)}"
                ),
            ),
        ]

    def _build_reduce_messages(
        self,
        summaries: list[str],
        symbol: str | None,
        max_summary_tokens: int | None,
    ) -> list[LLMMessage]:
        joined = "\n".join(f"- {summary}" for summary in summaries)
        return [
            LLMMessage(
                role="system",
                content=(
                    "You are a memory summarizer. Merge multiple chunk summaries "
                    "into one final context summary. Preserve non-duplicated "
                    "preferences, risks, and durable investment research conclusions. "
                    "Return concise plain text only."
                ),
            ),
            LLMMessage(
                role="user",
                content=(
                    f"symbol: {symbol or 'GLOBAL'}\n"
                    f"max_summary_tokens: {max_summary_tokens or 240}\n"
                    f"chunk_summaries:\n{joined}"
                ),
            ),
        ]

    def _format_memories(self, memories: list[MemoryRecordSchema]) -> str:
        return "\n".join(
            f"{index}. {memory.scope}/{memory.memory_type}: {memory.content}"
            for index, memory in enumerate(memories, start=1)
        )

    def _fallback_summary(self, memories: list[MemoryRecordSchema]) -> str:
        return " ".join(self._shorten(memory.content, limit=120) for memory in memories)

    def _merge_usage(self, total: dict[str, int], usage: dict[str, int]) -> None:
        total["prompt_tokens"] += usage.get("prompt_tokens", 0)
        total["completion_tokens"] += usage.get("completion_tokens", 0)
        total["total_tokens"] += usage.get("total_tokens", 0)
