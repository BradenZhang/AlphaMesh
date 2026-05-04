import json
import re

from app.services.llm.base import LLMProvider
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class MockLLMProvider(LLMProvider):
    def __init__(self, model: str = "mock-research-v1") -> None:
        self.model = model

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        if self._is_memory_summary_request(messages):
            return self._generate_memory_summary(messages)

        system_text = " ".join(
            m.content for m in messages if m.role == "system"
        ).lower()

        if "portfolio manager" in system_text:
            return self._generate_portfolio_manager(messages)

        symbol = self._extract_symbol(messages)
        payload = {
            "symbol": symbol,
            "summary": (
                f"{symbol} mock LLM analysis highlights resilient growth, "
                "stable profitability, and controlled leverage."
            ),
            "key_metrics": {
                "revenue_growth": 0.16,
                "net_margin": 0.21,
                "pe_ratio": 18.5,
                "llm_provider": "mock",
            },
            "valuation_view": "Mock LLM view: valuation is reasonable versus current growth.",
            "risks": [
                "Mock LLM output is deterministic and not based on live market news.",
                "Human review is required before any real investment decision.",
            ],
            "confidence_score": 0.73,
        }
        content = json.dumps(payload)
        return LLMResponse(
            content=content,
            provider="mock",
            model=self.model,
            usage={
                "prompt_tokens": sum(len(message.content.split()) for message in messages),
                "completion_tokens": len(content.split()),
                "total_tokens": sum(len(message.content.split()) for message in messages)
                + len(content.split()),
            },
            raw=content,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="mock", model=self.model, is_mock=True)

    def _extract_symbol(self, messages: list[LLMMessage]) -> str:
        text = "\n".join(message.content for message in messages)
        match = re.search(r"symbol\s*[:=]\s*([A-Za-z0-9._-]+)", text, re.IGNORECASE)
        return match.group(1).upper() if match else "UNKNOWN"

    def _generate_portfolio_manager(self, messages: list[LLMMessage]) -> LLMResponse:
        payload = {
            "decisions": [
                {
                    "symbol": "AAPL",
                    "action": "hold",
                    "target_weight": 0.3,
                    "rationale": (
                        "Mock portfolio manager: maintain current allocation "
                        "based on balanced research."
                    ),
                    "confidence_score": 0.7,
                },
            ],
            "portfolio_context_summary": (
                "Mock portfolio manager synthesis: portfolio is well-diversified "
                "with moderate concentration. Research signals are balanced."
            ),
            "concentration_warnings": [],
            "sector_exposure_notes": ["Technology sector is within acceptable limits."],
            "cash_ratio_note": "Cash ratio is healthy at approximately 80% of portfolio value.",
            "overall_confidence": 0.68,
        }
        content = json.dumps(payload)
        prompt_tokens = sum(len(m.content.split()) for m in messages)
        completion_tokens = len(content.split())
        return LLMResponse(
            content=content,
            provider="mock",
            model=self.model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            raw=content,
        )

    def _is_memory_summary_request(self, messages: list[LLMMessage]) -> bool:
        text = "\n".join(message.content for message in messages).lower()
        return "memory summarizer" in text

    def _generate_memory_summary(self, messages: list[LLMMessage]) -> LLMResponse:
        source = "\n".join(message.content for message in messages if message.role == "user")
        content_lines = [
            line.strip(" -")
            for line in source.splitlines()
            if line.strip() and not line.lower().startswith(("symbol:", "chunk_", "max_"))
        ]
        summary = "Mock memory summary: " + " ".join(content_lines[:4])
        if len(summary) > 520:
            summary = f"{summary[:517]}..."
        prompt_tokens = sum(len(message.content.split()) for message in messages)
        completion_tokens = len(summary.split())
        return LLMResponse(
            content=summary,
            provider="mock",
            model=self.model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            raw=summary,
        )
