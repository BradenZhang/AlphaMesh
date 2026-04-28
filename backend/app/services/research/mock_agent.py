from app.schemas.research import ResearchReport
from app.services.research.base import ResearchAgent


class MockResearchAgent(ResearchAgent):
    def analyze(self, symbol: str) -> ResearchReport:
        normalized = symbol.upper()
        return ResearchReport(
            symbol=normalized,
            summary=(
                f"{normalized} shows resilient revenue growth and stable profitability "
                "in mock data."
            ),
            key_metrics={
                "revenue_growth": 0.16,
                "net_margin": 0.21,
                "pe_ratio": 18.5,
                "debt_to_equity": 0.38,
            },
            valuation_view="Valuation is reasonable versus growth under the MVP mock assumptions.",
            risks=[
                "Mock data cannot reflect real market liquidity or news shocks.",
                "Strategy output requires human review before any real-world use.",
            ],
            confidence_score=0.72,
        )
