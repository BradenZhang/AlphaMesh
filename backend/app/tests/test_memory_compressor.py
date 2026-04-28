from datetime import UTC, datetime

from app.schemas.memory import MemoryRecordSchema
from app.services.llm.providers.mock_provider import MockLLMProvider
from app.services.memory.compressor import ContextCompressor
from app.services.memory.token_budget import TokenBudgetManager


def _memory(index: int, content: str | None = None) -> MemoryRecordSchema:
    return MemoryRecordSchema(
        memory_id=f"mem-test-{index}",
        scope="short_term",
        memory_type="conversation",
        symbol="MAPRED",
        user_id="default",
        content=content or f"旧消息 {index}: 偏好低回撤和现金流稳定。",
        importance_score=0.5,
        token_estimate=40,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )


def test_map_reduce_compressor_uses_one_map_call_for_single_chunk() -> None:
    compressor = ContextCompressor(llm_provider=MockLLMProvider(), chunk_size=5)

    summary = compressor.compress_map_reduce([_memory(index) for index in range(1, 4)])

    assert "Mock memory summary" in summary
    assert compressor.last_metadata["map_calls"] == 1
    assert compressor.last_metadata["reduce_calls"] == 0
    assert compressor.last_metadata["token_usage"]["total_tokens"] > 0


def test_map_reduce_compressor_reduces_multiple_chunk_summaries() -> None:
    compressor = ContextCompressor(llm_provider=MockLLMProvider(), chunk_size=5)

    summary = compressor.compress_map_reduce([_memory(index) for index in range(1, 14)])

    assert "Mock memory summary" in summary
    assert compressor.last_metadata["map_calls"] == 3
    assert compressor.last_metadata["reduce_calls"] == 1
    assert compressor.last_metadata["chunk_count"] == 3


def test_token_budget_triggers_compression_at_eighty_percent() -> None:
    manager = TokenBudgetManager(default_budget=100)

    assert not manager.should_compress(79)
    assert manager.should_compress(80)
    assert manager.allocate(100)["compression_trigger"] == 80
