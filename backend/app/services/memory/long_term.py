from app.schemas.memory import MemoryRecordSchema, MemoryWriteRequest
from app.services.memory.store import MemoryStore


class LongTermMemory:
    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def remember(
        self,
        content: str,
        symbol: str | None = None,
        memory_type: str = "research_summary",
        metadata: dict[str, object] | None = None,
        importance_score: float = 0.75,
    ) -> MemoryRecordSchema:
        return self.store.write(
            MemoryWriteRequest(
                scope="long_term",
                memory_type=memory_type,
                symbol=symbol,
                content=content,
                metadata=metadata or {},
                importance_score=importance_score,
            )
        )
