from app.schemas.agents import AgentFinding, InvestmentCommitteeReport, MultiAgentResearchReport
from app.schemas.research import ResearchReport
from app.services.agents.runtime import AgentRuntime
from app.services.case.store import InvestmentCaseStore


class MultiAgentResearchWorkflow:
    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self.runtime = runtime or AgentRuntime()
        self.case_store = InvestmentCaseStore()

    def run(self, symbol: str) -> MultiAgentResearchReport:
        normalized = symbol.upper()
        findings = [
            self.runtime.run_financial_statement_agent(normalized),
            self.runtime.run_valuation_agent(normalized),
            self.runtime.run_industry_agent(normalized),
            self.runtime.run_news_agent(normalized),
        ]
        committee_report = self.runtime.run_investment_committee(normalized, findings)
        research_report = self.to_research_report(normalized, findings, committee_report)
        case = self.case_store.create(
            symbol=normalized,
            thesis=research_report.summary,
            confidence=committee_report.confidence_score,
            risks=research_report.risks,
            data_sources=research_report.data_sources,
            decision=committee_report.action_bias.lower(),
        )
        report = MultiAgentResearchReport(
            symbol=normalized,
            findings=findings,
            committee_report=committee_report,
            research_report=research_report,
            case_id=case.case_id,
            market_provider=getattr(self.runtime.tool_registry, "provider_name", None),
        )
        provider_info = self.runtime.llm_provider.get_provider_info()
        self.runtime.run_logger.record(
            run_type="research",
            status="success",
            symbol=normalized,
            provider=provider_info.provider,
            model=provider_info.model,
            input_payload={"symbol": normalized, "workflow": "multi_agent"},
            output_payload=research_report.model_dump(mode="json"),
            market_provider=getattr(self.runtime.tool_registry, "provider_name", None),
        )
        return report

    def to_research_report(
        self,
        symbol: str,
        findings: list[AgentFinding],
        committee_report: InvestmentCommitteeReport,
    ) -> ResearchReport:
        key_metrics: dict[str, float | str] = {
            "committee_confidence": committee_report.confidence_score,
            "agent_count": len(findings),
            "action_bias": committee_report.action_bias,
        }
        for finding in findings:
            for key, value in finding.metrics.items():
                key_metrics[f"{finding.agent_name.lower().replace(' ', '_')}_{key}"] = value

        risks = []
        for finding in findings:
            risks.extend(finding.risks)

        data_sources: list[str] = []
        for finding in findings:
            for source in finding.data_sources:
                if source not in data_sources:
                    data_sources.append(source)

        return ResearchReport(
            symbol=symbol.upper(),
            summary=committee_report.summary,
            key_metrics=key_metrics,
            valuation_view=committee_report.consensus_view,
            risks=risks or ["Multi-agent workflow did not identify explicit risks."],
            confidence_score=committee_report.confidence_score,
            data_sources=data_sources,
        )
