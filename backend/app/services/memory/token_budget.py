from app.schemas.memory import MemoryRecordSchema


class TokenBudgetManager:
    def __init__(self, default_budget: int = 900, compression_threshold: float = 0.8) -> None:
        self.default_budget = default_budget
        self.compression_threshold = compression_threshold

    def estimate(self, text: str) -> int:
        normalized = text.strip()
        if not normalized:
            return 0
        # CJK characters are ~1-2 tokens each; Latin words are ~1 token per 4 chars.
        cjk_count = sum(1 for ch in normalized if "一" <= ch <= "鿿")
        non_cjk_len = len(normalized) - cjk_count
        return max(1, cjk_count + non_cjk_len // 4)

    def trim(
        self,
        memories: list[MemoryRecordSchema],
        budget: int | None = None,
    ) -> list[MemoryRecordSchema]:
        remaining = budget or self.default_budget
        selected: list[MemoryRecordSchema] = []
        for memory in memories:
            if memory.token_estimate <= remaining:
                selected.append(memory)
                remaining -= memory.token_estimate
        return selected

    def should_compress(self, token_estimate: int, budget: int | None = None) -> bool:
        active_budget = budget or self.default_budget
        if active_budget <= 0:
            return False
        return token_estimate >= int(active_budget * self.compression_threshold)

    def allocate(
        self,
        total_budget: int | None = None,
        history_ratio: float = 0.6,
        summary_ratio: float = 0.25,
    ) -> dict[str, int]:
        active_budget = total_budget or self.default_budget
        history_budget = int(active_budget * history_ratio)
        summary_budget = int(active_budget * summary_ratio)
        reserved_budget = max(active_budget - history_budget - summary_budget, 0)
        return {
            "total": active_budget,
            "history": history_budget,
            "summary": summary_budget,
            "reserved": reserved_budget,
            "compression_trigger": int(active_budget * self.compression_threshold),
        }
