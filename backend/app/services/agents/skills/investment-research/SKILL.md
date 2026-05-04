---
name: investment-research
description: Build a disciplined equity research view from quote, fundamentals, filings, news, sentiment, and macro context.
---

# Investment Research Skill

Use this skill when the user asks for an investment view, thesis, catalyst check, or multi-source stock analysis.

Process:
1. Start with the user's question and symbol.
2. Pull only the data needed for the question.
3. Separate observed data from inference.
4. State the thesis, supporting evidence, contrary evidence, and uncertainty.
5. Do not present demo, mock, or incomplete data as live market truth.
6. End with a concise non-advice decision framing: bias, confidence, and review needs.

Required output discipline:
- Cite tool names and provider names when available.
- Prefer short bullets over long prose.
- Mark stale, mock, or unavailable data explicitly.
- Never recommend live execution without a separate risk and approval step.
