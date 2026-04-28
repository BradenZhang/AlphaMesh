from app.services.agents.research_workflow import MultiAgentResearchWorkflow
from app.services.agents.run_logger import AgentRunLogger


def test_multi_agent_workflow_returns_complete_report() -> None:
    report = MultiAgentResearchWorkflow().run("AAPL")

    assert report.symbol == "AAPL"
    assert len(report.findings) == 4
    assert {finding.agent_name for finding in report.findings} == {
        "Financial Statement Agent",
        "Valuation Agent",
        "Industry Agent",
        "News Agent",
    }
    assert report.committee_report.summary
    assert report.research_report.symbol == "AAPL"
    assert report.research_report.key_metrics["agent_count"] == 4


def test_multi_agent_workflow_writes_agent_run_records() -> None:
    MultiAgentResearchWorkflow().run("MSFT")

    runs = AgentRunLogger().list_recent(limit=20)
    run_types = {run.run_type for run in runs if run.symbol == "MSFT"}

    assert "financial_statement_agent" in run_types
    assert "valuation_agent" in run_types
    assert "industry_agent" in run_types
    assert "news_agent" in run_types
    assert "investment_committee_agent" in run_types
    assert "research" in run_types
