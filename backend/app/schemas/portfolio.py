from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import PortfolioDecisionAction

# ── Watchlist ──────────────────────────────────────────────


class WatchlistItemCreate(BaseModel):
    symbol: str
    label: str | None = None
    sector: str | None = None
    industry: str | None = None
    notes: str | None = None


class WatchlistItemSchema(BaseModel):
    item_id: str
    symbol: str
    label: str | None = None
    sector: str | None = None
    industry: str | None = None
    user_id: str
    added_at: datetime
    notes: str | None = None


class WatchlistResponse(BaseModel):
    items: list[WatchlistItemSchema]


# ── Portfolio Holdings ─────────────────────────────────────


class PortfolioHoldingSchema(BaseModel):
    holding_id: str
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    sector: str | None = None
    industry: str | None = None
    weight: float


class PortfolioSummary(BaseModel):
    total_market_value: float
    total_cash: float
    total_portfolio_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    holdings: list[PortfolioHoldingSchema]
    sector_breakdown: dict[str, float]
    industry_breakdown: dict[str, float]
    holding_count: int


# ── Portfolio Manager ──────────────────────────────────────


class PortfolioDecision(BaseModel):
    symbol: str
    action: PortfolioDecisionAction
    target_weight: float = Field(ge=0, le=1)
    rationale: str
    confidence_score: float = Field(ge=0, le=1)


class PortfolioManagerReport(BaseModel):
    decisions: list[PortfolioDecision]
    portfolio_context_summary: str
    concentration_warnings: list[str] = Field(default_factory=list)
    sector_exposure_notes: list[str] = Field(default_factory=list)
    cash_ratio_note: str
    overall_confidence: float = Field(ge=0, le=1)


# ── Rebalance ──────────────────────────────────────────────


class RebalanceOrder(BaseModel):
    symbol: str
    side: str
    quantity: float
    estimated_amount: float
    target_weight: float
    current_weight: float
    rationale: str


class RebalanceProposal(BaseModel):
    orders: list[RebalanceOrder]
    estimated_turnover: float
    cash_after: float
    rationale: str


class RebalanceRiskReview(BaseModel):
    approved: bool
    risk_level: str
    reasons: list[str] = Field(default_factory=list)
    flagged_orders: list[str] = Field(default_factory=list)


class RebalanceRunRequest(BaseModel):
    user_id: str = "default"
    llm_profile_id: str | None = None
    max_orders: int = Field(default=10, ge=1, le=50)
    force: bool = False


class RebalanceWorkflowResult(BaseModel):
    run_id: str
    watchlist_symbols: list[str]
    research_reports: dict[str, object] = Field(default_factory=dict)
    portfolio_summary: PortfolioSummary | None = None
    portfolio_manager_report: PortfolioManagerReport | None = None
    rebalance_proposal: RebalanceProposal | None = None
    risk_review: RebalanceRiskReview | None = None
    executed_orders: list[object] = Field(default_factory=list)
    run_steps: list[object] = Field(default_factory=list)
    message: str
