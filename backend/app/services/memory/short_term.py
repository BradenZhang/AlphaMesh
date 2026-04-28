from app.schemas.memory import MemoryRecordSchema, MemoryWriteRequest
from app.services.memory.store import MemoryStore


class ShortTermMemory:
    def __init__(self, store: MemoryStore | None = None, ttl_seconds: int = 86_400) -> None:
        self.store = store or MemoryStore()
        self.ttl_seconds = ttl_seconds

    def remember(
        self,
        content: str,
        symbol: str | None = None,
        memory_type: str = "conversation",
        metadata: dict[str, object] | None = None,
        importance_score: float = 0.45,
    ) -> MemoryRecordSchema:
        return self.store.write(
            MemoryWriteRequest(
                scope="short_term",
                memory_type=memory_type,
                symbol=symbol,
                content=content,
                metadata=metadata or {},
                importance_score=importance_score,
                ttl_seconds=self.ttl_seconds,
            )
        )
