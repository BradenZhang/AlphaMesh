import time
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.core.exceptions import LiveTradingDisabledError
from app.domain.enums import AutomationMode, OrderSide, SignalAction
from app.schemas.agents import AgentReviewBundle
from app.schemas.automation import AutomationRunRequest, AutomationRunResponse
from app.schemas.common import RunStep, StepTracker
from app.schemas.order import OrderRequest
from app.schemas.risk import RiskCheckRequest
from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.run_logger import AgentRunLogger
from app.services.agents.runtime import AgentRuntime
from app.services.agents.tool_registry import ToolRegistry
from app.services.automation.base import AutomationFlowBase
from app.services.automation.checkpoint import CheckpointStore
from app.services.backtest.engine import BacktestEngine
from app.services.broker.base import BrokerAdapter
from app.services.broker.factory import get_broker_adapter
from app.services.broker.mock_broker import MockBrokerAdapter
from app.services.case.store import InvestmentCaseStore
from app.services.connectors.factory import get_account_connector
from app.services.explain.signal_explainer import SignalExplainer
from app.services.llm.factory import get_llm_provider_for_profile
from app.services.market.base import MarketSkillProvider
from app.services.market.factory import get_market_provider
from app.services.research.base import ResearchAgent
from app.services.risk.guard import RiskGuard
from app.services.strategy.factory import get_strategy


class AutomationFlow(AutomationFlowBase):
    def __init__(
        self,
        market_provider: MarketSkillProvider | None = None,
        market_provider_name: str = "mock",
        research_agent: ResearchAgent | None = None,
        broker_adapter: BrokerAdapter | None = None,
        settings: Settings | None = None,
        run_logger: AgentRunLogger | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.market_provider = market_provider or get_market_provider(market_provider_name)
        self.research_agent = research_agent
        self.broker_adapter = broker_adapter or MockBrokerAdapter()
        self.backtest_engine = BacktestEngine()
        self.risk_guard = RiskGuard(self.settings)
        self.explainer = SignalExplainer()
        self.run_logger = run_logger or AgentRunLogger()
        self.case_store = InvestmentCaseStore()
        self.checkpoint_store = CheckpointStore()

    def run(
        self,
        request: AutomationRunRequest,
        *,
        run_id: str | None = None,
        resume: bool = False,
        replay: bool = False,
    ) -> AutomationRunResponse:
        started_at = time.perf_counter()
        run_id = run_id or f"run-{uuid4().hex}"
        symbol = request.symbol.upper()
        market_provider_name = request.market_provider or getattr(
            self.market_provider, "provider_name", "mock"
        )
        execution_provider_name = request.execution_provider or getattr(
            self.broker_adapter, "provider_name", "mock"
        )
        account_provider_name = request.account_provider or market_provider_name
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

        if replay:
            self.checkpoint_store.clear(run_id)

        cached_steps: dict[str, object] = {}
        if resume:
            cached_steps = self.checkpoint_store.get_completed_steps(run_id)

        tracker = StepTracker()
        cp = self._make_checkpoint_runner(run_id, cached_steps, tracker)
        self.market_provider = tracker.run_step(
            "provider_resolution",
            "Resolve market provider",
            lambda: get_market_provider(market_provider_name),
        )
        self.broker_adapter = tracker.run_step(
            "execution_resolution",
            "Resolve execution provider",
            lambda: (
                get_broker_adapter(execution_provider_name)
                if request.mode != AutomationMode.MANUAL
                else self.broker_adapter
            ),
        )
        account_snapshot = cp(
            "account_snapshot",
            "Load account snapshot",
            lambda: get_account_connector(account_provider_name).get_account_snapshot(),
        )

        quote = cp(
            "market_quote",
            "Fetch live quote",
            lambda: self.market_provider.get_quote(symbol),
        )
        kline = cp(
            "market_kline",
            "Fetch K-line bars",
            lambda: self.market_provider.get_kline(symbol),
        )
        fundamentals = cp(
            "market_fundamentals",
            "Fetch fundamentals",
            lambda: self.market_provider.get_fundamentals(symbol),
        )

        agent_runtime = AgentRuntime(
            llm_provider=get_llm_provider_for_profile(request.llm_profile_id, self.settings),
            tool_registry=ToolRegistry(market_provider=self.market_provider),
            run_logger=self.run_logger,
        )
        multi_agent_report = cp(
            "multi_agent_research", "Multi-agent research",
            lambda: MultiAgentResearchWorkflow(runtime=agent_runtime).run(symbol),
        )
        research_report = multi_agent_report.research_report

        strategy = get_strategy(request.strategy_name)
        strategy_signal = cp(
            "strategy_signal", "Generate strategy signal",
            lambda: strategy.generate_signal(
                symbol=symbol,
                bars=kline.bars,
                fundamentals=fundamentals,
                research_report=research_report,
            ),
        )
        backtest_result = cp(
            "backtest", "Run backtest",
            lambda: self.backtest_engine.run(
                symbol=symbol,
                bars=kline.bars,
                strategy_name=request.strategy_name,
                slippage_bps=request.slippage_bps,
                commission_per_trade=request.commission_per_trade,
                walk_forward=request.walk_forward,
                train_ratio=request.train_ratio,
            ),
        )
        strategy_review = cp(
            "strategy_review", "Strategy review",
            lambda: agent_runtime.run_strategy_review(
                symbol=symbol,
                research=research_report,
                signal=strategy_signal,
                backtest=backtest_result,
            ),
        )
        order_request = self._build_order_request(strategy_signal.action, symbol, quote.price)
        risk_result = cp(
            "risk_check", "Risk guard check",
            lambda: self.risk_guard.check(
                RiskCheckRequest(
                    signal=strategy_signal,
                    order_request=order_request,
                    backtest_result=backtest_result,
                    mode=request.mode,
                    current_position_pct=account_snapshot.positions.get(symbol, 0.0),
                )
            ),
        )
        risk_review = cp(
            "risk_review", "Risk review",
            lambda: agent_runtime.run_risk_review(
                symbol=symbol,
                signal=strategy_signal,
                risk_result=risk_result,
            ),
        )
        explanation = cp(
            "explanation", "Generate explanation",
            lambda: self.explainer.explain(
                research_report=research_report,
                strategy_signal=strategy_signal,
                backtest_result=backtest_result,
                risk_result=risk_result,
            ),
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
        if request.mode != AutomationMode.PAPER_AUTO:
            tracker.steps.append(
                RunStep(
                    step_id="order",
                    label="Submit paper order",
                    status="skipped",
                )
            )
        if request.mode == AutomationMode.PAPER_AUTO:
            if risk_result.approved and order_request is not None:
                order = cp(
                    "order", "Submit paper order",
                    lambda: self.broker_adapter.submit_order(order_request),
                )
                executed = True
                message = "Paper auto mode submitted a mock order."
            else:
                tracker.steps.append(
                    RunStep(
                        step_id="order",
                        label="Submit paper order",
                        status="skipped",
                    )
                )
                message = (
                    "Paper auto mode did not submit an order because risk or signal blocked it."
                )

        case = self.case_store.create(
            symbol=symbol,
            thesis=research_report.summary,
            confidence=multi_agent_report.committee_report.confidence_score,
            risks=research_report.risks,
            data_sources=research_report.data_sources,
            decision=strategy_signal.action.value.lower(),
            order_id=order.order_id if order else None,
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
            run_steps=tracker.steps,
            case_id=case.case_id,
            run_id=run_id,
            market_provider=market_provider_name,
            execution_provider=execution_provider_name,
            account_provider=account_provider_name,
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
            run_id=run_id,
            market_provider=market_provider_name,
            execution_provider=execution_provider_name,
            account_provider=account_provider_name,
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
            broker=getattr(self.broker_adapter, "provider_name", None),
            environment=(
                "live"
                if getattr(self.broker_adapter, "provider_name", "mock") != "mock"
                else "paper"
            ),
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
            market_provider=request.market_provider,
            execution_provider=request.execution_provider,
            account_provider=request.account_provider,
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    def _make_checkpoint_runner(
        self,
        run_id: str,
        cached_steps: dict[str, object],
        tracker: StepTracker,
    ):
        def cp(step_id: str, label: str, fn):
            cached = cached_steps.get(step_id)
            if cached is not None:
                output = cached.output_snapshot if hasattr(cached, "output_snapshot") else cached
                tracker.steps.append(RunStep(
                    step_id=step_id,
                    label=label,
                    status="completed",
                    summary="Resumed from checkpoint",
                ))
                return output

            step_started = time.perf_counter()
            self.checkpoint_store.save(
                run_id=run_id, step_id=step_id, step_label=label, status="running",
                started_at=datetime.now(UTC).replace(tzinfo=None),
            )
            try:
                result = fn()
                duration_ms = int((time.perf_counter() - step_started) * 1000)
                if hasattr(result, "model_dump"):
                    output_payload = result.model_dump(mode="json")
                else:
                    output_payload = {"value": str(result)[:500]}
                self.checkpoint_store.save(
                    run_id=run_id, step_id=step_id, step_label=label, status="completed",
                    output_snapshot=output_payload,
                    completed_at=datetime.now(UTC).replace(tzinfo=None),
                    duration_ms=duration_ms,
                )
                tracker.steps.append(RunStep(
                    step_id=step_id,
                    label=label,
                    status="completed",
                    started_at=datetime.now(UTC).replace(tzinfo=None),
                    completed_at=datetime.now(UTC).replace(tzinfo=None),
                    duration_ms=duration_ms,
                ))
                return result
            except Exception as exc:
                duration_ms = int((time.perf_counter() - step_started) * 1000)
                self.checkpoint_store.save(
                    run_id=run_id, step_id=step_id, step_label=label, status="failed",
                    error=str(exc),
                    completed_at=datetime.now(UTC).replace(tzinfo=None),
                    duration_ms=duration_ms,
                )
                tracker.steps.append(RunStep(
                    step_id=step_id,
                    label=label,
                    status="failed",
                    error=str(exc),
                    started_at=datetime.now(UTC).replace(tzinfo=None),
                    completed_at=datetime.now(UTC).replace(tzinfo=None),
                    duration_ms=duration_ms,
                ))
                raise

        return cp
