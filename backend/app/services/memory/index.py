from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import AgentMemoryRecord
from app.db.session import SessionLocal
from app.services.memory.tokenizer import jaccard_similarity, tokenize_text


@dataclass(slots=True)
class IndexedMemory:
    memory_id: str
    user_id: str
    symbol: str | None
    memory_type: str
    content: str
    keywords: list[str]
    importance_score: float
    token_estimate: int
    created_at: datetime
    expires_at: datetime | None


@dataclass(slots=True)
class MemorySearchHit:
    memory_id: str
    score: float
    matched_keywords: list[str]


class MemoryIndex:
    def __init__(self) -> None:
        self._records: dict[str, IndexedMemory] = {}
        self._lock = RLock()
        self.loaded_at: datetime | None = None

    def load_long_term_memories(self) -> int:
        now = datetime.now(UTC).replace(tzinfo=None)
        with SessionLocal() as session:
            records = (
                session.query(AgentMemoryRecord)
                .filter(
                    AgentMemoryRecord.scope == "long_term",
                    or_(
                        AgentMemoryRecord.expires_at.is_(None),
                        AgentMemoryRecord.expires_at > now,
                    ),
                )
                .all()
            )

        with self._lock:
            self._records = {
                record.memory_id: self._from_record(record)
                for record in records
            }
            self.loaded_at = now
            return len(self._records)

    def upsert(self, record: AgentMemoryRecord) -> None:
        if record.scope != "long_term":
            return
        with self._lock:
            self._records[record.memory_id] = self._from_record(record)

    def remove(self, memory_id: str) -> None:
        with self._lock:
            self._records.pop(memory_id, None)

    def remove_expired(self) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        with self._lock:
            expired_ids = [
                memory_id
                for memory_id, record in self._records.items()
                if record.expires_at is not None and record.expires_at < now
            ]
            for memory_id in expired_ids:
                self._records.pop(memory_id, None)

    def search(
        self,
        query: str | None = None,
        symbol: str | None = None,
        user_id: str = "default",
        limit: int = 12,
    ) -> list[MemorySearchHit]:
        query_tokens = tokenize_text(query or "")
        normalized_symbol = symbol.upper() if symbol else None
        now = datetime.now(UTC).replace(tzinfo=None)
        hits: list[MemorySearchHit] = []

        with self._lock:
            records = list(self._records.values())

        for record in records:
            if record.user_id != user_id:
                continue
            if normalized_symbol and record.symbol not in {normalized_symbol, None}:
                continue
            if record.expires_at is not None and record.expires_at < now:
                continue
            matched = sorted(set(query_tokens) & set(record.keywords))
            if query_tokens and not matched:
                continue
            keyword_score = (
                len(matched) / max(len(set(query_tokens)), 1)
                if query_tokens
                else 0.0
            )
            score = (
                keyword_score * 0.6
                + record.importance_score * 0.3
                + self._recency_score(record.created_at, now) * 0.1
            )
            hits.append(
                MemorySearchHit(
                    memory_id=record.memory_id,
                    score=round(score, 6),
                    matched_keywords=matched,
                )
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[: max(1, min(limit, 100))]

    def stats(self) -> dict[str, int | str | None]:
        with self._lock:
            keywords = {
                keyword
                for record in self._records.values()
                for keyword in record.keywords
            }
            return {
                "index_loaded_count": len(self._records),
                "index_keyword_count": len(keywords),
                "index_loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            }

    def similarity_search(
        self,
        keywords: list[str],
        symbol: str | None,
        user_id: str,
        memory_type: str,
        threshold: float = 0.85,
    ) -> str | None:
        normalized_symbol = symbol.upper() if symbol else None
        best_memory_id: str | None = None
        best_score = 0.0

        with self._lock:
            records = list(self._records.values())

        for record in records:
            if record.user_id != user_id or record.memory_type != memory_type:
                continue
            if record.symbol != normalized_symbol:
                continue
            score = jaccard_similarity(keywords, record.keywords)
            if score > best_score:
                best_score = score
                best_memory_id = record.memory_id

        return best_memory_id if best_score >= threshold else None

    def load_from_session(self, session: Session) -> int:
        now = datetime.now(UTC).replace(tzinfo=None)
        records = (
            session.query(AgentMemoryRecord)
            .filter(
                AgentMemoryRecord.scope == "long_term",
                or_(AgentMemoryRecord.expires_at.is_(None), AgentMemoryRecord.expires_at > now),
            )
            .all()
        )
        with self._lock:
            self._records = {
                record.memory_id: self._from_record(record)
                for record in records
            }
            self.loaded_at = now
            return len(self._records)

    def _from_record(self, record: AgentMemoryRecord) -> IndexedMemory:
        keywords = record.token_keywords or tokenize_text(record.content)
        return IndexedMemory(
            memory_id=record.memory_id,
            user_id=record.user_id,
            symbol=record.symbol,
            memory_type=record.memory_type,
            content=record.content,
            keywords=keywords,
            importance_score=record.importance_score,
            token_estimate=record.token_estimate,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

    def _recency_score(self, created_at: datetime, now: datetime) -> float:
        age_days = max((now - created_at).total_seconds() / 86400, 0)
        return 1 / (1 + age_days / 30)


memory_index = MemoryIndex()


def get_memory_index() -> MemoryIndex:
    return memory_index
