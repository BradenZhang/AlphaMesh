from app.schemas.backtest import BacktestResult
from app.schemas.research import ResearchReport
from app.schemas.risk import RiskResult
from app.schemas.strategy import StrategySignal
from app.services.explain.base import SignalExplainerBase


class SignalExplainer(SignalExplainerBase):
    def explain(
        self,
        research_report: ResearchReport,
        strategy_signal: StrategySignal,
        backtest_result: BacktestResult,
        risk_result: RiskResult,
    ) -> str:
        return (
            f"{strategy_signal.symbol} 当前策略建议为 {strategy_signal.action}. "
            f"策略理由：{strategy_signal.reason} "
            f"研究摘要：{research_report.summary} "
            f"回测总收益 {backtest_result.total_return:.2%}，"
            f"最大回撤 {backtest_result.max_drawdown:.2%}，"
            f"胜率 {backtest_result.win_rate:.2%}。"
            f"风控结论：{risk_result.risk_level}，"
            f"{'允许继续' if risk_result.approved else '不建议自动执行'}。"
        )
