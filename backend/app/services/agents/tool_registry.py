from datetime import date

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

    def run_tool(self, tool_name: str, payload: dict[str, object]) -> dict[str, object]:
        normalized_tool = tool_name.strip().lower()
        symbol = str(payload.get("symbol") or "").upper()
        if not symbol:
            return self._error_observation(normalized_tool, "Tool payload requires symbol.")

        if normalized_tool == "get_quote":
            quote = self.market_provider.get_quote(symbol)
            return {
                "success": True,
                "summary": f"{symbol} quote is {quote.price} from {quote.provider}.",
                "data": quote.model_dump(mode="json"),
            }

        if normalized_tool == "get_kline":
            kline = self.market_provider.get_kline(
                symbol=symbol,
                start=self._parse_date(payload.get("start")),
                end=self._parse_date(payload.get("end")),
                interval=str(payload.get("interval") or "1d"),
            )
            return {
                "success": True,
                "summary": f"{symbol} kline returned {len(kline.bars)} bars.",
                "data": {
                    "symbol": kline.symbol,
                    "interval": kline.interval,
                    "bars": [bar.model_dump(mode="json") for bar in kline.bars[-10:]],
                    "bar_count": len(kline.bars),
                    "provider": kline.provider,
                },
            }

        if normalized_tool == "get_fundamentals":
            fundamentals = self.market_provider.get_fundamentals(symbol)
            return {
                "success": True,
                "summary": (
                    f"{symbol} fundamentals include PE {fundamentals.pe_ratio} "
                    f"and revenue growth {fundamentals.revenue_growth:.2%}."
                ),
                "data": fundamentals.model_dump(mode="json"),
            }

        if normalized_tool == "get_market_context":
            context = self.get_market_context(symbol)
            return {
                "success": True,
                "summary": f"{symbol} market context includes quote and fundamentals.",
                "data": context,
            }

        return self._error_observation(
            normalized_tool,
            f"Tool '{tool_name}' is not allowed in ReAct-lite.",
        )

    def _error_observation(self, tool_name: str, message: str) -> dict[str, object]:
        return {
            "success": False,
            "summary": message,
            "data": {"tool_name": tool_name},
        }

    def _parse_date(self, value: object) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None
