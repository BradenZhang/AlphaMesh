from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import desc, func, or_

from app.db.init_db import init_db
from app.db.models import AgentMemoryRecord
from app.db.session import SessionLocal
from app.schemas.memory import (
    MemoryContextResponse,
    MemoryRecordSchema,
    MemoryStatsResponse,
    MemoryWriteRequest,
)
from app.services.memory.compressor import ContextCompressor
from app.services.memory.index import get_memory_index
from app.services.memory.token_budget import TokenBudgetManager
from app.services.memory.tokenizer import (
    content_hash,
    jaccard_similarity,
    tokenize_text,
)


class MemoryStore:
    def __init__(
        self,
        compressor: ContextCompressor | None = None,
        token_budget: TokenBudgetManager | None = None,
    ) -> None:
        self.compressor = compressor or ContextCompressor()
        self.token_budget = token_budget or TokenBudgetManager()

    def write(self, request: MemoryWriteRequest) -> MemoryRecordSchema:
        init_db()
        now = datetime.now(UTC).replace(tzinfo=None)
        normalized_symbol = request.symbol.upper() if request.symbol else None
        normalized_hash = content_hash(request.content)
        token_keywords = tokenize_text(request.content)
        expires_at = (
            now + timedelta(seconds=request.ttl_seconds)
            if request.ttl_seconds is not None
            else None
        )
        with SessionLocal() as session:
            if request.scope == "long_term":
                duplicate = self._find_exact_duplicate(
                    session=session,
                    request=request,
                    normalized_symbol=normalized_symbol,
                    normalized_hash=normalized_hash,
                )
                if duplicate is not None:
                    return self._update_duplicate(
                        session=session,
                        record=duplicate,
                        request=request,
                        now=now,
                        token_keywords=token_keywords,
                        normalized_hash=normalized_hash,
                        reason="exact",
                    )

                similar = self._find_similar_duplicate(
                    session=session,
                    request=request,
                    normalized_symbol=normalized_symbol,
                    token_keywords=token_keywords,
                )
                if similar is not None:
                    return self._update_duplicate(
                        session=session,
                        record=similar,
                        request=request,
                        now=now,
                        token_keywords=token_keywords,
                        normalized_hash=normalized_hash,
                        reason="similar",
                    )

            record = AgentMemoryRecord(
                memory_id=f"mem-{uuid4().hex}",
                scope=request.scope,
                memory_type=request.memory_type,
                symbol=normalized_symbol,
                user_id=request.user_id,
                content=request.content,
                content_hash=normalized_hash,
                token_keywords=token_keywords,
                metadata_payload=request.metadata,
                importance_score=request.importance_score,
                token_estimate=self.token_budget.estimate(request.content),
                expires_at=expires_at,
                created_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            if record.scope == "long_term":
                get_memory_index().upsert(record)
            return self._to_schema(record)

    def list_recent(
        self,
        limit: int = 20,
        user_id: str = "default",
        scope: str | None = None,
        symbol: str | None = None,
    ) -> list[MemoryRecordSchema]:
        init_db()
        self.cleanup_expired()
        normalized_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            query = session.query(AgentMemoryRecord).filter(AgentMemoryRecord.user_id == user_id)
            if scope:
                query = query.filter(AgentMemoryRecord.scope == scope)
            if symbol:
                query = query.filter(AgentMemoryRecord.symbol == symbol.upper())
            records = (
                query.order_by(desc(AgentMemoryRecord.created_at))
                .limit(normalized_limit)
                .all()
            )
            return [self._to_schema(record) for record in records]

    def search_context(
        self,
        symbol: str | None = None,
        user_id: str = "default",
        query: str | None = None,
        limit: int = 12,
        token_budget: int | None = None,
    ) -> MemoryContextResponse:
        init_db()
        self.cleanup_expired()
        normalized_symbol = symbol.upper() if symbol else None
        normalized_limit = max(1, min(limit, 100))
        index_hits = get_memory_index().search(
            query=query or normalized_symbol,
            symbol=normalized_symbol,
            user_id=user_id,
            limit=normalized_limit * 2,
        )
        index_scores = {hit.memory_id: hit.score for hit in index_hits}
        with SessionLocal() as session:
            base_query = session.query(AgentMemoryRecord).filter(
                AgentMemoryRecord.user_id == user_id
            )
            if normalized_symbol:
                base_query = base_query.filter(
                    or_(
                        AgentMemoryRecord.symbol == normalized_symbol,
                        AgentMemoryRecord.symbol.is_(None),
                    )
                )

            short_records = (
                base_query.filter(AgentMemoryRecord.scope == "short_term")
                .order_by(
                    desc(AgentMemoryRecord.importance_score),
                    desc(AgentMemoryRecord.created_at),
                )
                .limit(normalized_limit)
                .all()
            )
            if index_scores:
                long_records = (
                    base_query.filter(
                        AgentMemoryRecord.scope == "long_term",
                        AgentMemoryRecord.memory_id.in_(index_scores),
                    )
                    .all()
                )
            else:
                long_records = (
                    base_query.filter(AgentMemoryRecord.scope == "long_term")
                    .order_by(
                        desc(AgentMemoryRecord.importance_score),
                        desc(AgentMemoryRecord.created_at),
                    )
                    .limit(normalized_limit)
                    .all()
                )

            scored_memories = [
                (
                    self._to_schema(record),
                    self._memory_score(
                        record,
                        query=query,
                        index_score=index_scores.get(record.memory_id),
                    ),
                )
                for record in [*short_records, *long_records]
            ]

        scored_memories.sort(key=lambda item: item[1], reverse=True)
        memories = [memory for memory, _ in scored_memories[:normalized_limit]]
        active_budget = token_budget or self.token_budget.default_budget
        budget_allocation = self.token_budget.allocate(active_budget)
        raw_token_estimate = sum(memory.token_estimate for memory in memories)
        compression_triggered = self.token_budget.should_compress(
            raw_token_estimate,
            active_budget,
        )
        if compression_triggered:
            trimmed = memories
            context = self.compressor.compress_map_reduce(
                memories,
                symbol=normalized_symbol,
                max_summary_tokens=budget_allocation["summary"],
            )
            context_token_estimate = self.token_budget.estimate(context)
        else:
            trimmed = self.token_budget.trim(memories, budget_allocation["history"])
            context = self.compressor.compress(trimmed)
            context_token_estimate = sum(memory.token_estimate for memory in trimmed)

        compression_metadata = self.compressor.last_metadata
        return MemoryContextResponse(
            symbol=normalized_symbol,
            user_id=user_id,
            query=query,
            context=context,
            memories=trimmed,
            token_budget=active_budget,
            token_estimate=context_token_estimate,
            compacted=compression_triggered or len(trimmed) < len(memories),
            compression_triggered=compression_triggered,
            compression_strategy=str(compression_metadata.get("strategy", "direct")),
            budget_allocation=budget_allocation,
            compression_token_usage=dict(
                compression_metadata.get(
                    "token_usage",
                    {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                )
            ),
        )

    def compact(self, symbol: str | None = None, user_id: str = "default") -> MemoryRecordSchema:
        context = self.search_context(symbol=symbol, user_id=user_id, limit=20, token_budget=700)
        return self.write(
            MemoryWriteRequest(
                scope="long_term",
                memory_type="research_summary",
                symbol=symbol,
                user_id=user_id,
                content=f"Compacted memory context:\n{context.context}",
                metadata={"source": "manual_compact", "memory_count": len(context.memories)},
                importance_score=0.78,
            )
        )

    def stats(self, user_id: str = "default") -> MemoryStatsResponse:
        init_db()
        self.cleanup_expired()
        with SessionLocal() as session:
            short_count = (
                session.query(func.count(AgentMemoryRecord.id))
                .filter(
                    AgentMemoryRecord.user_id == user_id,
                    AgentMemoryRecord.scope == "short_term",
                )
                .scalar()
                or 0
            )
            long_count = (
                session.query(func.count(AgentMemoryRecord.id))
                .filter(
                    AgentMemoryRecord.user_id == user_id,
                    AgentMemoryRecord.scope == "long_term",
                )
                .scalar()
                or 0
            )
            total_tokens = (
                session.query(func.sum(AgentMemoryRecord.token_estimate))
                .filter(AgentMemoryRecord.user_id == user_id)
                .scalar()
                or 0
            )
        index_stats = get_memory_index().stats()
        return MemoryStatsResponse(
            short_term_count=short_count,
            long_term_count=long_count,
            total_count=short_count + long_count,
            total_token_estimate=total_tokens,
            index_loaded_count=int(index_stats["index_loaded_count"] or 0),
            index_keyword_count=int(index_stats["index_keyword_count"] or 0),
            index_loaded_at=index_stats["index_loaded_at"],
        )

    def cleanup_expired(self) -> int:
        init_db()
        now = datetime.now(UTC).replace(tzinfo=None)
        with SessionLocal() as session:
            deleted = (
                session.query(AgentMemoryRecord)
                .filter(
                    AgentMemoryRecord.expires_at.is_not(None),
                    AgentMemoryRecord.expires_at < now,
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            if deleted:
                get_memory_index().remove_expired()
            return deleted

    def _to_schema(self, record: AgentMemoryRecord) -> MemoryRecordSchema:
        return MemoryRecordSchema(
            memory_id=record.memory_id,
            scope=record.scope,
            memory_type=record.memory_type,
            symbol=record.symbol,
            user_id=record.user_id,
            content=record.content,
            content_hash=record.content_hash or content_hash(record.content),
            token_keywords=record.token_keywords or tokenize_text(record.content),
            metadata=record.metadata_payload or {},
            importance_score=record.importance_score,
            token_estimate=record.token_estimate,
            expires_at=record.expires_at,
            created_at=record.created_at,
        )

    def _find_exact_duplicate(
        self,
        session,
        request: MemoryWriteRequest,
        normalized_symbol: str | None,
        normalized_hash: str,
    ) -> AgentMemoryRecord | None:
        return (
            session.query(AgentMemoryRecord)
            .filter(
                AgentMemoryRecord.user_id == request.user_id,
                AgentMemoryRecord.scope == request.scope,
                AgentMemoryRecord.symbol.is_(None)
                if normalized_symbol is None
                else AgentMemoryRecord.symbol == normalized_symbol,
                AgentMemoryRecord.memory_type == request.memory_type,
                AgentMemoryRecord.content_hash == normalized_hash,
            )
            .order_by(desc(AgentMemoryRecord.created_at))
            .first()
        )

    def _find_similar_duplicate(
        self,
        session,
        request: MemoryWriteRequest,
        normalized_symbol: str | None,
        token_keywords: list[str],
    ) -> AgentMemoryRecord | None:
        memory_id = get_memory_index().similarity_search(
            keywords=token_keywords,
            symbol=normalized_symbol,
            user_id=request.user_id,
            memory_type=request.memory_type,
        )
        if memory_id is not None:
            return (
                session.query(AgentMemoryRecord)
                .filter(AgentMemoryRecord.memory_id == memory_id)
                .first()
            )

        candidates = (
            session.query(AgentMemoryRecord)
            .filter(
                AgentMemoryRecord.user_id == request.user_id,
                AgentMemoryRecord.scope == request.scope,
                AgentMemoryRecord.symbol.is_(None)
                if normalized_symbol is None
                else AgentMemoryRecord.symbol == normalized_symbol,
                AgentMemoryRecord.memory_type == request.memory_type,
            )
            .order_by(desc(AgentMemoryRecord.created_at))
            .limit(50)
            .all()
        )
        for candidate in candidates:
            candidate_keywords = candidate.token_keywords or tokenize_text(candidate.content)
            if jaccard_similarity(token_keywords, candidate_keywords) >= 0.85:
                return candidate
        return None

    def _update_duplicate(
        self,
        session,
        record: AgentMemoryRecord,
        request: MemoryWriteRequest,
        now: datetime,
        token_keywords: list[str],
        normalized_hash: str,
        reason: str,
    ) -> MemoryRecordSchema:
        metadata = dict(record.metadata_payload or {})
        metadata.update(request.metadata)
        metadata.update({"deduplicated": True, "dedupe_reason": reason})
        record.metadata_payload = metadata
        record.importance_score = max(record.importance_score, request.importance_score)
        record.created_at = now
        record.content_hash = record.content_hash or normalized_hash
        record.token_keywords = record.token_keywords or token_keywords
        session.commit()
        session.refresh(record)
        get_memory_index().upsert(record)
        return self._to_schema(record)

    def _memory_score(
        self,
        record: AgentMemoryRecord,
        query: str | None,
        index_score: float | None = None,
    ) -> float:
        if index_score is not None:
            return index_score
        now = datetime.now(UTC).replace(tzinfo=None)
        query_tokens = tokenize_text(query or "")
        memory_tokens = record.token_keywords or tokenize_text(record.content)
        keyword_score = jaccard_similarity(query_tokens, memory_tokens) if query_tokens else 0.0
        age_days = max((now - record.created_at).total_seconds() / 86400, 0)
        recency_score = 1 / (1 + age_days / 30)
        return keyword_score * 0.5 + record.importance_score * 0.4 + recency_score * 0.1
