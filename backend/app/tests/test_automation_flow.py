import pytest

from app.core.exceptions import LiveTradingDisabledError
from app.domain.enums import AutomationMode
from app.schemas.automation import AutomationRunRequest
from app.services.automation.flow import AutomationFlow


def test_automation_flow_manual_mode_returns_plan_only() -> None:
    result = AutomationFlow().run(
        AutomationRunRequest(symbol="AAPL", mode=AutomationMode.MANUAL)
    )

    assert result.symbol == "AAPL"
    assert result.mode == AutomationMode.MANUAL
    assert result.executed is False
    assert result.order is None
    assert result.multi_agent_report is not None
    assert len(result.multi_agent_report.findings) == 4
    assert result.agent_reviews is not None
    assert result.agent_reviews.strategy_review.review_summary
    assert result.agent_reviews.risk_review.review_summary
    assert result.explanation


def test_automation_flow_paper_auto_submits_mock_order() -> None:
    result = AutomationFlow().run(
        AutomationRunRequest(symbol="AAPL", mode=AutomationMode.PAPER_AUTO)
    )

    assert result.mode == AutomationMode.PAPER_AUTO
    assert result.executed is True
    assert result.order is not None
    assert result.order.paper is True
    assert result.order.order_id.startswith("paper-")


def test_automation_flow_accepts_llm_profile_id() -> None:
    result = AutomationFlow().run(
        AutomationRunRequest(
            symbol="MSFT",
            mode=AutomationMode.MANUAL,
            llm_profile_id="mock",
        )
    )

    assert result.symbol == "MSFT"
    assert result.multi_agent_report is not None
    assert result.agent_reviews is not None


def test_automation_flow_live_auto_disabled_by_default() -> None:
    with pytest.raises(LiveTradingDisabledError, match="disabled"):
        AutomationFlow().run(
            AutomationRunRequest(symbol="AAPL", mode=AutomationMode.LIVE_AUTO)
        )
