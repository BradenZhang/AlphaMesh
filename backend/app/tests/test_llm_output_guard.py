import pytest

from app.services.llm.output_guard import LLMOutputGuard, LLMOutputValidationError


def test_output_guard_parses_json_fenced_research_report() -> None:
    content = """```json
{
  "symbol": "aapl",
  "summary": "Valid summary",
  "key_metrics": {"pe_ratio": 18.5},
  "valuation_view": "Reasonable valuation",
  "risks": ["Mock risk"],
  "confidence_score": 0.7
}
```"""

    report = LLMOutputGuard().parse_research_report(content, expected_symbol="AAPL")

    assert report.symbol == "AAPL"
    assert report.confidence_score == 0.7


def test_output_guard_rejects_missing_risks() -> None:
    content = """
{
  "symbol": "AAPL",
  "summary": "Valid summary",
  "key_metrics": {"pe_ratio": 18.5},
  "valuation_view": "Reasonable valuation",
  "risks": [],
  "confidence_score": 0.7
}
"""

    with pytest.raises(LLMOutputValidationError, match="risks"):
        LLMOutputGuard().parse_research_report(content, expected_symbol="AAPL")
