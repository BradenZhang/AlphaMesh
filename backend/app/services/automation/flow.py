import time

from app.core.config import Settings, get_settings
from app.core.exceptions import LiveTradingDisabledError
from app.domain.enums import AutomationMode, OrderSide, SignalAction
from app.schemas.agents import AgentReviewBundle
from app.schemas.automation import AutomationRunRequest, AutomationRunResponse
from app.schemas.order import OrderRequest
from app.schemas.risk import RiskCheckRequest
from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.runtime import AgentRuntime
from app.services.automation.base import AutomationFlowBase
from app.services.backtest.engine import BacktestEngine
from app.services.broker.base import BrokerAdapter
from app.services.broker.mock_broker import MockBrokerAdapter
from app.services.explain.signal_explainer import SignalExplainer
from app.services.llm.factory import get_llm_provider_for_profile
from app.services.market.base import MarketSkillProvider
from app.services.market.mock_provider import MockSkillProvider
from app.services.research.base import ResearchAgent
from app.services.risk.guard import RiskGuard
from app.services.strategy.factory import get_strategy


class AutomationFlow(AutomationFlowBase):
    def __init__(
        self,
        market_provider: MarketSkillProvider | None = None,
        research_agent: ResearchAgent | None = None,
        broker_adapter: BrokerAdapter | None = None,
        settings: Settings | None = None,
        run_logger: AgentRunLogger | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.market_provider = market_provider or MockSkillProvider()
        self.research_agent = research_agent
        self.broker_adapter = broker_adapter or MockBrokerAdapter()
        self.backtest_engine = BacktestEngine()
        self.risk_guard = RiskGuard(self.settings)
        self.explainer = SignalExplainer()
        self.run_logger = run_logger or AgentRunLogger()

    def run(self, request: AutomationRunRequest) -> AutomationRunResponse:
        started_at = time.perf_counter()
        symbol = request.symbol.upper()
        if request.mode == AutomationMode.LIVE_AUTO and not self.settings.live_auto_enabled:
            self._log_failure(request, symbol, started_at, "live_auto is disabled by default.")
            raise LiveTradingDisabledError("live_auto is disabled by default in the MVP scaffold.")
        if request.mode == AutomationMode.LIVE_AUTO:
            self._log_failure(
                request,
                symbol,
                started_at,
                "live_auto has no real broker implementation.",
            )
            raise LiveTradingDisabledError(
                "live_auto has no real broker implementation in the MVP scaffold."
            )

        quote = self.market_provider.get_quote(symbol)
        kline = self.market_provider.get_kline(symbol)
        fundamentals = self.market_provider.get_fundamentals(symbol)
        agent_runtime = AgentRuntime(
            llm_provider=get_llm_provider_for_profile(request.llm_profile_id, self.settings),
            run_logger=self.run_logger,
        )
        multi_agent_report = MultiAgentResearchWorkflow(runtime=agent_runtime).run(symbol)
        research_report = multi_agent_report.research_report

        strategy = get_strategy(request.strategy_name)
        strategy_signal = strategy.generate_signal(
            symbol=symbol,
            bars=kline.bars,
            fundamentals=fundamentals,
            research_report=research_report,
        )
        backtest_result = self.backtest_engine.run(
            symbol=symbol,
            bars=kline.bars,
            strategy_name=request.strategy_name,
        )
        strategy_review = agent_runtime.run_strategy_review(
            symbol=symbol,
            research=research_report,
            signal=strategy_signal,
            backtest=backtest_result,
        )
        order_request = self._build_order_request(strategy_signal.action, symbol, quote.price)
        risk_result = self.risk_guard.check(
            RiskCheckRequest(
                signal=strategy_signal,
                order_request=order_request,
                backtest_result=backtest_result,
                mode=request.mode,
                current_position_pct=0.0,
            )
        )
        risk_review = agent_runtime.run_risk_review(
            symbol=symbol,
            signal=strategy_signal,
            risk_result=risk_result,
        )
        explanation = self.explainer.explain(
            research_report=research_report,
            strategy_signal=strategy_signal,
            backtest_result=backtest_result,
            risk_result=risk_result,
        )
        explanation = (
            f"{explanation} 多 Agent 委员会观点："
            f"{multi_agent_report.committee_report.consensus_view} "
            f"策略复核：{strategy_review.review_summary} "
            f"风控复核：{risk_review.review_summary}"
        )

        order = None
        executed = False
        message = "Manual mode returns a plan only; no order was submitted."
        if request.mode == AutomationMode.PAPER_AUTO:
            if risk_result.approved and order_request is not None:
                order = self.broker_adapter.submit_order(order_request)
                executed = True
                message = "Paper auto mode submitted a mock order."
            else:
                message = (
                    "Paper auto mode did not submit an order because risk or signal blocked it."
                )

        response = AutomationRunResponse(
            symbol=symbol,
            mode=request.mode,
            quote=quote,
            kline=kline,
            research_report=research_report,
            strategy_signal=strategy_signal,
            backtest_result=backtest_result,
            risk_result=risk_result,
            explanation=explanation,
            multi_agent_report=multi_agent_report,
            agent_reviews=AgentReviewBundle(
                strategy_review=strategy_review,
                risk_review=risk_review,
            ),
            order=order,
            executed=executed,
            message=message,
        )
        self.run_logger.record(
            run_type="automation",
            status="success",
            symbol=symbol,
            input_payload=request.model_dump(mode="json"),
            output_payload={
                "action": response.strategy_signal.action,
                "risk_level": response.risk_result.risk_level,
                "executed": response.executed,
                "order_id": response.order.order_id if response.order else None,
            },
            latency_ms=self._elapsed_ms(started_at),
        )
        return response

    def _build_order_request(
        self,
        action: SignalAction,
        symbol: str,
        price: float,
    ) -> OrderRequest | None:
        if action == SignalAction.HOLD:
            return None
        side = OrderSide.BUY if action == SignalAction.BUY else OrderSide.SELL
        quantity = 10.0
        return OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=round(price, 2),
            estimated_amount=round(price * quantity, 2),
        )

    def _log_failure(
        self,
        request: AutomationRunRequest,
        symbol: str,
        started_at: float,
        error_message: str,
    ) -> None:
        self.run_logger.record(
            run_type="automation",
            status="failed",
            symbol=symbol,
            input_payload=request.model_dump(mode="json"),
            error_message=error_message,
            latency_ms=self._elapsed_ms(started_at),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)
