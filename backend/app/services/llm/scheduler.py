"""Task-complexity-based LLM model scheduler.

Maps agent task types to complexity levels, then selects an LLM profile
based on complexity. Simple tasks use cheap models, complex synthesis/risk
tasks use stronger models.
"""

from dataclasses import dataclass

from app.core.config import get_settings
from app.domain.enums import TaskComplexity
from app.services.llm.base import LLMProvider
from app.services.llm.factory import get_llm_provider_for_profile

# Task type → complexity mapping
TASK_COMPLEXITY_MAP: dict[str, TaskComplexity] = {
    # Simple: data extraction, summarization
    "data_extraction": TaskComplexity.SIMPLE,
    "summarization": TaskComplexity.SIMPLE,
    "news_agent": TaskComplexity.SIMPLE,
    "industry_agent": TaskComplexity.SIMPLE,
    # Moderate: analysis, research
    "financial_statement_agent": TaskComplexity.MODERATE,
    "valuation_agent": TaskComplexity.MODERATE,
    "research": TaskComplexity.MODERATE,
    # Complex: synthesis, risk review, portfolio management
    "investment_committee_agent": TaskComplexity.COMPLEX,
    "portfolio_manager_agent": TaskComplexity.COMPLEX,
    "strategy_review_agent": TaskComplexity.COMPLEX,
    "risk_review_agent": TaskComplexity.COMPLEX,
    "rebalance_review": TaskComplexity.COMPLEX,
}

DEFAULT_COMPLEXITY = TaskComplexity.MODERATE


@dataclass
class SchedulerResult:
    provider: LLMProvider
    complexity: TaskComplexity
    profile_id: str | None
    reason: str


class ModelScheduler:
    def get_provider_for_task(
        self,
        task_type: str,
        override_profile_id: str | None = None,
    ) -> SchedulerResult:
        if override_profile_id:
            provider = get_llm_provider_for_profile(override_profile_id)
            complexity = TASK_COMPLEXITY_MAP.get(task_type, DEFAULT_COMPLEXITY)
            return SchedulerResult(
                provider=provider,
                complexity=complexity,
                profile_id=override_profile_id,
                reason=f"Explicit profile override: {override_profile_id}",
            )

        complexity = TASK_COMPLEXITY_MAP.get(task_type, DEFAULT_COMPLEXITY)
        settings = get_settings()

        profile_id_map = {
            TaskComplexity.SIMPLE: settings.scheduler_simple_profile,
            TaskComplexity.MODERATE: settings.scheduler_moderate_profile,
            TaskComplexity.COMPLEX: settings.scheduler_complex_profile,
        }
        profile_id = profile_id_map.get(complexity)

        if profile_id:
            provider = get_llm_provider_for_profile(profile_id)
            reason = f"Scheduled {complexity.value} task '{task_type}' to profile '{profile_id}'"
        else:
            provider = get_llm_provider_for_profile()
            reason = f"No {complexity.value} profile configured, using default for '{task_type}'"

        return SchedulerResult(
            provider=provider,
            complexity=complexity,
            profile_id=profile_id,
            reason=reason,
        )
