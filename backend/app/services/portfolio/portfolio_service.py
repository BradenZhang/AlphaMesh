from app.schemas.portfolio import PortfolioHoldingSchema, PortfolioSummary
from app.services.market.base import MarketSkillProvider
from app.services.market.factory import get_market_provider
from app.services.portfolio.holding_store import PortfolioHoldingStore


class PortfolioService:
    def __init__(
        self,
        holding_store: PortfolioHoldingStore | None = None,
        market_provider: MarketSkillProvider | None = None,
    ) -> None:
        self.holding_store = holding_store or PortfolioHoldingStore()
        self.market_provider = market_provider or get_market_provider("mock")

    def get_summary(self, user_id: str = "default") -> PortfolioSummary:
        holdings = self.holding_store.list_holdings(user_id)

        prices: dict[str, float] = {}
        for h in holdings:
            try:
                quote = self.market_provider.get_quote(h.symbol)
                prices[h.symbol] = quote.price
            except Exception:
                prices[h.symbol] = h.current_price
        if prices:
            self.holding_store.update_prices(prices)

        holdings = self.holding_store.list_holdings(user_id)

        total_market_value = 0.0
        sector_totals: dict[str, float] = {}
        industry_totals: dict[str, float] = {}

        for h in holdings:
            total_market_value += h.market_value
            if h.sector:
                sector_totals[h.sector] = sector_totals.get(h.sector, 0.0) + h.market_value
            if h.industry:
                industry_totals[h.industry] = industry_totals.get(h.industry, 0.0) + h.market_value

        try:
            account = self.market_provider.get_account_snapshot()
            cash = account.cash
        except Exception:
            cash = 100_000.0

        total_portfolio_value = total_market_value + cash
        total_unrealized_pnl = sum(h.unrealized_pnl for h in holdings)
        total_cost = sum(h.quantity * h.avg_cost for h in holdings)
        total_unrealized_pnl_pct = total_unrealized_pnl / total_cost if total_cost else 0.0

        weighted_holdings: list[PortfolioHoldingSchema] = []
        for h in holdings:
            weight = h.market_value / total_portfolio_value if total_portfolio_value else 0.0
            weighted_holdings.append(h.model_copy(update={"weight": round(weight, 4)}))

        sector_breakdown = {
            k: round(v / total_portfolio_value, 4) if total_portfolio_value else 0.0
            for k, v in sector_totals.items()
        }
        industry_breakdown = {
            k: round(v / total_portfolio_value, 4) if total_portfolio_value else 0.0
            for k, v in industry_totals.items()
        }

        return PortfolioSummary(
            total_market_value=round(total_market_value, 2),
            total_cash=round(cash, 2),
            total_portfolio_value=round(total_portfolio_value, 2),
            total_unrealized_pnl=round(total_unrealized_pnl, 2),
            total_unrealized_pnl_pct=round(total_unrealized_pnl_pct, 4),
            holdings=weighted_holdings,
            sector_breakdown=sector_breakdown,
            industry_breakdown=industry_breakdown,
            holding_count=len(holdings),
        )
