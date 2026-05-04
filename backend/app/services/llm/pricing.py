# Approximate pricing per 1M tokens (USD) as of early 2026.
# These are estimates for cost monitoring, not billing-grade.

PRICING_TABLE: dict[tuple[str, str], tuple[float, float]] = {
    # (provider, model) -> (input_rate_per_1m, output_rate_per_1m)
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("openai", "gpt-4-turbo"): (10.00, 30.00),
    ("openai", "gpt-3.5-turbo"): (0.50, 1.50),
    ("anthropic", "claude-sonnet-4-20250514"): (3.00, 15.00),
    ("anthropic", "claude-3-5-haiku-20241022"): (0.80, 4.00),
    ("anthropic", "claude-3-opus-20240229"): (15.00, 75.00),
    ("gemini", "gemini-1.5-pro"): (3.50, 10.50),
    ("gemini", "gemini-1.5-flash"): (0.075, 0.30),
    ("gemini", "gemini-2.0-flash"): (0.10, 0.40),
    ("deepseek", "deepseek-chat"): (0.14, 0.28),
    ("deepseek", "deepseek-reasoner"): (0.55, 2.19),
}

DEFAULT_RATE = (3.00, 15.00)


def estimate_cost_usd(
    provider: str | None,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Estimate the cost of an LLM call in USD."""
    key = ((provider or "").lower(), (model or "").lower())
    input_rate, output_rate = PRICING_TABLE.get(key, DEFAULT_RATE)
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000
