from datetime import date
from uuid import uuid4

from app.schemas.harness import PlanStepSchema, PlanUpdateRequest
from app.services.agents.skill_loader import AgentSkillLoader, get_agent_skill_loader
from app.services.harness.plans import AgentPlanStore
from app.services.market.base import MarketSkillProvider
from app.services.market.factory import get_market_provider


class ToolRegistry:
    """Read-only harness tools exposed to investment agents."""

    def __init__(
        self,
        market_provider: MarketSkillProvider | None = None,
        market_provider_name: str | None = None,
        skill_loader: AgentSkillLoader | None = None,
        plan_store: AgentPlanStore | None = None,
        plan_id: str | None = None,
    ) -> None:
        self.market_provider = market_provider or (
            get_market_provider(market_provider_name)
            if market_provider_name is not None
            else get_market_provider()
        )
        self.provider_name = getattr(self.market_provider, "provider_name", "unknown")
        self.skill_loader = skill_loader or get_agent_skill_loader()
        self.plan_store = plan_store or AgentPlanStore()
        self.plan_id = plan_id or f"plan-{uuid4().hex}"

    def get_tool_manifest(self) -> list[dict[str, object]]:
        return [
            {
                "name": "load_skill",
                "description": "Load full instructions for one available domain skill.",
                "requires_symbol": False,
            },
            {
                "name": "list_skills",
                "description": "List available domain skills and short descriptions.",
                "requires_symbol": False,
            },
            {
                "name": "todo_update",
                "description": (
                    "Create or update the current plan. Only one step may be in_progress."
                ),
                "requires_symbol": False,
            },
            {
                "name": "todo_get",
                "description": "Read the current plan state.",
                "requires_symbol": False,
            },
            {
                "name": "get_quote",
                "description": "Fetch latest quote snapshot for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_kline",
                "description": "Fetch historical bars for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_fundamentals",
                "description": "Fetch valuation and financial metrics for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_market_context",
                "description": "Fetch quote, fundamentals, news, sentiment, filings, and macro.",
                "requires_symbol": True,
            },
            {
                "name": "get_filings",
                "description": "Fetch recent filings for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_news",
                "description": "Fetch recent news for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_sentiment",
                "description": "Fetch sentiment score for a symbol.",
                "requires_symbol": True,
            },
            {
                "name": "get_macro",
                "description": "Fetch macro indicators for a region.",
                "requires_symbol": False,
            },
        ]

    def get_skill_descriptions(self) -> str:
        return self.skill_loader.descriptions()

    def get_market_context(self, symbol: str) -> dict[str, object]:
        quote = self.market_provider.get_quote(symbol)
        fundamentals = self.market_provider.get_fundamentals(symbol)
        news = self.market_provider.get_news(symbol)
        sentiment = self.market_provider.get_sentiment(symbol)
        filings = self.market_provider.get_filings(symbol)
        macro = self.market_provider.get_macro()
        return {
            "quote": quote.model_dump(mode="json"),
            "fundamentals": fundamentals.model_dump(mode="json"),
            "news": news.model_dump(mode="json"),
            "sentiment": sentiment.model_dump(mode="json"),
            "filings": filings.model_dump(mode="json"),
            "macro": macro.model_dump(mode="json"),
        }

    def run_tool(self, tool_name: str, payload: dict[str, object]) -> dict[str, object]:
        normalized_tool = tool_name.strip().lower()

        if normalized_tool == "list_skills":
            skills = self.skill_loader.list_skills()
            return {
                "success": True,
                "summary": f"{len(skills)} domain skills are available.",
                "data": {"skills": skills},
            }

        if normalized_tool == "load_skill":
            skill_name = str(payload.get("name") or payload.get("skill_name") or "").strip()
            if not skill_name:
                return self._error_observation(normalized_tool, "Tool payload requires skill name.")
            content = self.skill_loader.get_content(skill_name)
            success = not content.startswith("Error:")
            return {
                "success": success,
                "summary": (
                    f"Loaded skill '{skill_name}'."
                    if success
                    else content
                ),
                "data": {
                    "skill_name": skill_name,
                    "content": content,
                    "content_chars": len(content),
                },
            }

        if normalized_tool == "todo_update":
            raw_steps = payload.get("steps")
            if not isinstance(raw_steps, list):
                return self._error_observation(normalized_tool, "Tool payload requires steps list.")
            try:
                steps = [PlanStepSchema.model_validate(step) for step in raw_steps]
                plan = self.plan_store.update_plan(
                    PlanUpdateRequest(
                        plan_id=str(payload.get("plan_id") or self.plan_id),
                        owner_type=str(payload.get("owner_type") or "react"),
                        owner_id=str(payload.get("owner_id") or ""),
                        symbol=str(payload.get("symbol") or "") or None,
                        steps=steps,
                    )
                )
            except ValueError as exc:
                return self._error_observation(normalized_tool, str(exc))
            self.plan_id = plan.plan_id
            return {
                "success": True,
                "summary": f"Plan {plan.plan_id} updated with {len(plan.steps)} steps.",
                "data": plan.model_dump(mode="json"),
            }

        if normalized_tool == "todo_get":
            plan_id = str(payload.get("plan_id") or self.plan_id)
            plan = self.plan_store.get_plan(plan_id)
            if plan is None:
                return self._error_observation(normalized_tool, f"Plan '{plan_id}' not found.")
            return {
                "success": True,
                "summary": f"Plan {plan.plan_id} has {len(plan.steps)} steps.",
                "data": plan.model_dump(mode="json"),
            }

        if normalized_tool == "get_macro":
            region = str(payload.get("region") or "US")
            macro = self.market_provider.get_macro(region=region)
            return {
                "success": True,
                "summary": (
                    f"Macro indicators for {macro.region}: "
                    f"{len(macro.indicators)} indicators."
                ),
                "data": {**macro.model_dump(mode="json"), "market_provider": self.provider_name},
            }

        symbol = str(payload.get("symbol") or "").upper()
        if not symbol:
            return self._error_observation(normalized_tool, "Tool payload requires symbol.")

        if normalized_tool == "get_quote":
            quote = self.market_provider.get_quote(symbol)
            return {
                "success": True,
                "summary": f"{symbol} quote is {quote.price} from {quote.provider}.",
                "data": {**quote.model_dump(mode="json"), "market_provider": self.provider_name},
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
                    "market_provider": self.provider_name,
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
                "data": {
                    **fundamentals.model_dump(mode="json"),
                    "market_provider": self.provider_name,
                },
            }

        if normalized_tool == "get_market_context":
            context = self.get_market_context(symbol)
            return {
                "success": True,
                "summary": (
                    f"{symbol} market context includes quote, fundamentals, news, "
                    "sentiment, filings, and macro."
                ),
                "data": {**context, "market_provider": self.provider_name},
            }

        if normalized_tool == "get_filings":
            limit = int(payload.get("limit") or 5)
            filings = self.market_provider.get_filings(symbol, limit=limit)
            return {
                "success": True,
                "summary": f"{symbol} filings returned {len(filings.filings)} items.",
                "data": {**filings.model_dump(mode="json"), "market_provider": self.provider_name},
            }

        if normalized_tool == "get_news":
            limit = int(payload.get("limit") or 10)
            news = self.market_provider.get_news(symbol, limit=limit)
            return {
                "success": True,
                "summary": f"{symbol} news returned {len(news.items)} items.",
                "data": {**news.model_dump(mode="json"), "market_provider": self.provider_name},
            }

        if normalized_tool == "get_sentiment":
            sentiment = self.market_provider.get_sentiment(symbol)
            return {
                "success": True,
                "summary": f"{symbol} sentiment score is {sentiment.score}.",
                "data": {
                    **sentiment.model_dump(mode="json"),
                    "market_provider": self.provider_name,
                },
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
