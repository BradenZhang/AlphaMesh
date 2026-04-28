from app.services.market.base import MarketSkillProvider
from app.services.market.mock_provider import MockSkillProvider


class ToolRegistry:
    """Read-only tools exposed to LLM agents in the MVP."""

    def __init__(self, market_provider: MarketSkillProvider | None = None) -> None:
        self.market_provider = market_provider or MockSkillProvider()

    def get_market_context(self, symbol: str) -> dict[str, object]:
        quote = self.market_provider.get_quote(symbol)
        fundamentals = self.market_provider.get_fundamentals(symbol)
        return {
            "quote": quote.model_dump(mode="json"),
            "fundamentals": fundamentals.model_dump(mode="json"),
        }
