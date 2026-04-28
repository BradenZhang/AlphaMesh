from uuid import uuid4

from app.schemas.memory import MemoryWriteRequest
from app.services.agents.react_runtime import ReActRuntime
from app.services.memory.store import MemoryStore


def test_memory_store_writes_and_builds_context() -> None:
    store = MemoryStore()
    symbol = "MEMCTX"
    record = store.write(
        MemoryWriteRequest(
            scope="short_term",
            memory_type="conversation",
            symbol=symbol,
            content="User prefers conservative position sizing for MEMCTX research.",
            importance_score=0.7,
        )
    )

    context = store.search_context(symbol=symbol)

    assert record.memory_id.startswith("mem-")
    assert context.symbol == symbol
    assert any(memory.memory_id == record.memory_id for memory in context.memories)
    assert "conservative position sizing" in context.context


def test_memory_compact_creates_long_term_summary() -> None:
    store = MemoryStore()
    store.write(
        MemoryWriteRequest(
            scope="short_term",
            memory_type="research_summary",
            symbol="MSFT",
            content="MSFT mock memory for compaction test.",
            importance_score=0.6,
        )
    )

    compacted = store.compact(symbol="MSFT")

    assert compacted.scope == "long_term"
    assert compacted.memory_type == "research_summary"
    assert "Compacted memory context" in compacted.content


def test_react_runtime_writes_trace_memory() -> None:
    result = ReActRuntime().run("NVDA", llm_profile_id="mock")

    memories = MemoryStore().list_recent(limit=10, symbol="NVDA")

    assert result.steps
    assert any(memory.memory_type == "react_trace" for memory in memories)


def test_long_term_memory_exact_duplicate_is_deduplicated() -> None:
    store = MemoryStore()
    symbol = f"DUP{uuid4().hex[:6]}".upper()
    request = MemoryWriteRequest(
        scope="long_term",
        memory_type="preference",
        symbol=symbol,
        content="用户偏好低回撤和估值安全边际。",
        importance_score=0.6,
    )

    first = store.write(request)
    second = store.write(request)

    assert second.memory_id == first.memory_id
    assert second.metadata["deduplicated"] is True
    assert second.metadata["dedupe_reason"] == "exact"
    assert second.content_hash == first.content_hash


def test_long_term_memory_similar_duplicate_updates_existing_record() -> None:
    store = MemoryStore()
    symbol = f"SIM{uuid4().hex[:6]}".upper()
    first = store.write(
        MemoryWriteRequest(
            scope="long_term",
            memory_type="preference",
            symbol=symbol,
            content="用户偏好低回撤策略，关注估值安全边际。",
            importance_score=0.5,
        )
    )
    second = store.write(
        MemoryWriteRequest(
            scope="long_term",
            memory_type="preference",
            symbol=symbol,
            content="用户偏好低回撤策略，关注估值安全边际!",
            importance_score=0.8,
        )
    )

    assert second.memory_id == first.memory_id
    assert second.importance_score == 0.8
    assert second.metadata["deduplicated"] is True
    assert second.metadata["dedupe_reason"] == "similar"


def test_long_term_memory_is_searchable_immediately_with_chinese_query() -> None:
    store = MemoryStore()
    symbol = f"CN{uuid4().hex[:6]}".upper()
    record = store.write(
        MemoryWriteRequest(
            scope="long_term",
            memory_type="preference",
            symbol=symbol,
            content="中文长期记忆：偏好低回撤、现金流稳定、估值安全边际。",
            importance_score=0.75,
        )
    )

    context = store.search_context(symbol=symbol, query="低回撤 估值安全边际")

    assert context.query == "低回撤 估值安全边际"
    assert any(memory.memory_id == record.memory_id for memory in context.memories)
    assert "低回撤" in context.context


def test_memory_context_triggers_map_reduce_when_budget_usage_is_high() -> None:
    store = MemoryStore()
    symbol = f"MR{uuid4().hex[:6]}".upper()
    repeated_context = "偏好低回撤、估值安全边际、现金流稳定，并要求人工复核。"
    for index in range(9):
        store.write(
            MemoryWriteRequest(
                scope="short_term",
                memory_type="conversation",
                symbol=symbol,
                content=f"{index}: {repeated_context * 12}",
                importance_score=0.6,
            )
        )

    context = store.search_context(symbol=symbol, limit=20, token_budget=900)

    assert context.compression_triggered is True
    assert context.compression_strategy == "map_reduce"
    assert context.budget_allocation["compression_trigger"] == 720
    assert context.compression_token_usage["total_tokens"] > 0
