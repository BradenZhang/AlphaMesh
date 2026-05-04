import time
from uuid import uuid4

from app.schemas.order import OrderRequest
from app.schemas.portfolio import (
    PortfolioManagerReport,
    PortfolioSummary,
    RebalanceOrder,
    RebalanceProposal,
    RebalanceRunRequest,
    RebalanceWorkflowResult,
)
from app.services.agents.runtime import AgentRuntime
from app.services.broker.mock_broker import MockBrokerAdapter
from app.services.portfolio.batch_research import BatchResearchService
from app.services.portfolio.portfolio_service import PortfolioService
from app.services.portfolio.watchlist_store import WatchlistStore
from app.services.risk.guard import RiskGuard


class RebalanceWorkflow:
    def __init__(
        self,
        runtime: AgentRuntime | None = None,
        portfolio_service: PortfolioService | None = None,
        watchlist_store: WatchlistStore | None = None,
        risk_guard: RiskGuard | None = None,
        broker: MockBrokerAdapter | None = None,
    ) -> None:
        self.runtime = runtime or AgentRuntime()
        self.portfolio_service = portfolio_service or PortfolioService()
        self.watchlist_store = watchlist_store or WatchlistStore()
        self.risk_guard = risk_guard or RiskGuard()
        self.broker = broker or MockBrokerAdapter()

    def run(self, request: RebalanceRunRequest) -> RebalanceWorkflowResult:
        run_id = f"rebal-{uuid4().hex}"
        run_steps: list[dict[str, object]] = []
        started = time.perf_counter()

        # Step 1: Load watchlist
        step_start = time.perf_counter()
        watchlist_items = self.watchlist_store.list_items(request.user_id)
        symbols = [item.symbol for item in watchlist_items]
        run_steps.append({
            "step": "load_watchlist",
            "status": "success",
            "symbols": symbols,
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        if not symbols:
            return RebalanceWorkflowResult(
                run_id=run_id,
                watchlist_symbols=[],
                message="Watchlist is empty. Add symbols before running rebalance.",
                run_steps=run_steps,
            )

        # Step 2: Batch research
        step_start = time.perf_counter()
        batch_service = BatchResearchService(runtime=self.runtime)
        research_reports = batch_service.run_all(symbols)
        run_steps.append({
            "step": "batch_research",
            "status": "success",
            "symbols_researched": list(research_reports.keys()),
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        # Step 3: Portfolio summary
        step_start = time.perf_counter()
        portfolio_summary = self.portfolio_service.get_summary(request.user_id)
        run_steps.append({
            "step": "portfolio_summary",
            "status": "success",
            "holding_count": portfolio_summary.holding_count,
            "total_value": portfolio_summary.total_portfolio_value,
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        # Step 4: Portfolio manager agent
        step_start = time.perf_counter()
        pm_report = self.runtime.run_portfolio_manager_agent(
            research_reports=research_reports,
            portfolio_summary=portfolio_summary,
        )
        run_steps.append({
            "step": "portfolio_manager",
            "status": "success",
            "decision_count": len(pm_report.decisions),
            "overall_confidence": pm_report.overall_confidence,
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        # Step 5: Build rebalance proposal
        step_start = time.perf_counter()
        proposal = self._build_proposal(
            pm_report=pm_report,
            portfolio_summary=portfolio_summary,
            max_orders=request.max_orders,
        )
        run_steps.append({
            "step": "rebalance_proposal",
            "status": "success",
            "order_count": len(proposal.orders),
            "estimated_turnover": proposal.estimated_turnover,
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        # Step 6: Risk review
        step_start = time.perf_counter()
        risk_review = self.risk_guard.check_rebalance(proposal, portfolio_summary)
        run_steps.append({
            "step": "risk_review",
            "status": "success",
            "approved": risk_review.approved,
            "risk_level": risk_review.risk_level,
            "latency_ms": int((time.perf_counter() - step_start) * 1000),
        })

        # Step 7: Execute orders (if approved)
        executed_orders: list[dict[str, object]] = []
        if risk_review.approved or request.force:
            step_start = time.perf_counter()
            for order in proposal.orders:
                try:
                    side = order.side.upper()
                    order_request = OrderRequest(
                        symbol=order.symbol,
                        side=side,
                        quantity=order.quantity,
                        limit_price=None,
                        estimated_amount=order.estimated_amount,
                    )
                    response = self.broker.submit_order(order_request)
                    executed_orders.append({
                        "order_id": response.order_id,
                        "symbol": response.symbol,
                        "side": response.side,
                        "quantity": response.quantity,
                        "status": response.status.value,
                    })
                except Exception as exc:
                    executed_orders.append({
                        "symbol": order.symbol,
                        "side": order.side,
                        "error": str(exc),
                    })
            run_steps.append({
                "step": "execute_orders",
                "status": "success",
                "executed_count": len(executed_orders),
                "latency_ms": int((time.perf_counter() - step_start) * 1000),
            })
        else:
            run_steps.append({
                "step": "execute_orders",
                "status": "skipped",
                "reason": "Risk review did not approve. Use force=True to override.",
            })

        total_ms = int((time.perf_counter() - started) * 1000)

        return RebalanceWorkflowResult(
            run_id=run_id,
            watchlist_symbols=symbols,
            research_reports={s: r.model_dump(mode="json") for s, r in research_reports.items()},
            portfolio_summary=portfolio_summary,
            portfolio_manager_report=pm_report,
            rebalance_proposal=proposal,
            risk_review=risk_review,
            executed_orders=executed_orders,
            run_steps=run_steps,
            message=f"Rebalance workflow completed in {total_ms}ms. "
            f"{len(executed_orders)} orders executed.",
        )

    def _build_proposal(
        self,
        pm_report: PortfolioManagerReport,
        portfolio_summary: PortfolioSummary,
        max_orders: int,
    ) -> RebalanceProposal:
        orders: list[RebalanceOrder] = []
        total_value = portfolio_summary.total_portfolio_value

        prices: dict[str, float] = {}
        for h in portfolio_summary.holdings:
            prices[h.symbol] = h.current_price

        current_weights: dict[str, float] = {}
        for h in portfolio_summary.holdings:
            current_weights[h.symbol] = h.weight

        for decision in pm_report.decisions[:max_orders]:
            symbol = decision.symbol
            target_weight = decision.target_weight
            current_weight = current_weights.get(symbol, 0.0)
            price = prices.get(symbol, 0.0)

            if price <= 0:
                continue

            target_value = total_value * target_weight
            current_value = total_value * current_weight
            delta_value = target_value - current_value

            if abs(delta_value) < 1.0:
                continue

            side = "BUY" if delta_value > 0 else "SELL"
            quantity = abs(delta_value) / price
            quantity = round(quantity, 2)

            if quantity < 0.01:
                continue

            orders.append(RebalanceOrder(
                symbol=symbol,
                side=side,
                quantity=quantity,
                estimated_amount=round(abs(delta_value), 2),
                target_weight=target_weight,
                current_weight=current_weight,
                rationale=decision.rationale,
            ))

        total_turnover = sum(o.estimated_amount for o in orders)
        turnover_pct = total_turnover / total_value if total_value else 0.0
        buy_total = sum(o.estimated_amount for o in orders if o.side == "BUY")
        sell_total = sum(o.estimated_amount for o in orders if o.side == "SELL")
        cash_after = portfolio_summary.total_cash + sell_total - buy_total

        return RebalanceProposal(
            orders=orders,
            estimated_turnover=round(turnover_pct, 4),
            cash_after=round(cash_after, 2),
            rationale=pm_report.portfolio_context_summary,
        )
