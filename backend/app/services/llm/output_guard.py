import json
import re

from pydantic import ValidationError

from app.schemas.research import ResearchReport


class LLMOutputValidationError(ValueError):
    pass


class LLMOutputGuard:
    def parse_research_report(self, content: str, expected_symbol: str) -> ResearchReport:
        payload = self._extract_json(content)
        payload.setdefault("symbol", expected_symbol.upper())
        payload["symbol"] = str(payload["symbol"]).upper()

        try:
            report = ResearchReport.model_validate(payload)
        except ValidationError as exc:
            raise LLMOutputValidationError(f"Invalid ResearchReport payload: {exc}") from exc

        if not report.summary.strip():
            raise LLMOutputValidationError("ResearchReport summary cannot be empty.")
        if not report.valuation_view.strip():
            raise LLMOutputValidationError("ResearchReport valuation_view cannot be empty.")
        if not report.risks:
            raise LLMOutputValidationError("ResearchReport risks cannot be empty.")

        return report

    def _extract_json(self, content: str) -> dict[str, object]:
        candidates = [content.strip()]
        fenced = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
        if fenced:
            candidates.insert(0, fenced.group(1).strip())

        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            candidates.append(content[start : end + 1])

        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload

        raise LLMOutputValidationError("LLM response did not contain a valid JSON object.")
