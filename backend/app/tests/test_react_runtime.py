import json

from app.services.agents.react_runtime import ReActRuntime
from app.services.agents.tool_registry import ToolRegistry
from app.services.llm.base import LLMProvider
from app.services.llm.schemas import LLMMessage, LLMProviderInfo, LLMResponse


class RecordingLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages_by_call: list[list[LLMMessage]] = []

    def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.2,
    ) -> LLMResponse:
        self.messages_by_call.append(messages)
        if len(self.messages_by_call) == 1:
            content = json.dumps({
                "action": "get_market_context",
                "action_input": {"symbol": "AAPL"},
                "rationale_summary": "Need a compact full context snapshot.",
            })
        else:
            content = json.dumps({
                "final_answer": "AAPL context reviewed.",
                "confidence_score": 0.66,
            })
        return LLMResponse(
            content=content,
            provider="recording",
            model="recording-model",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            raw=content,
        )

    def get_provider_info(self) -> LLMProviderInfo:
        return LLMProviderInfo(provider="recording", model="recording-model", is_mock=False)


def test_react_runtime_mock_returns_structured_trace() -> None:
    result = ReActRuntime().run("AAPL", llm_profile_id="mock")

    assert result.symbol == "AAPL"
    assert result.llm_profile_id == "mock"
    assert len(result.steps) >= 2
    assert result.steps[0].tool_call.tool_name == "get_quote"
    assert result.steps[0].observation.success is True
    assert result.final_answer


def test_tool_registry_rejects_unknown_react_tool() -> None:
    observation = ToolRegistry().run_tool("submit_order", {"symbol": "AAPL"})

    assert observation["success"] is False
    assert "not allowed" in str(observation["summary"])


def test_tool_registry_loads_domain_skill_without_symbol() -> None:
    observation = ToolRegistry().run_tool("load_skill", {"name": "investment-research"})

    assert observation["success"] is True
    assert observation["data"]["skill_name"] == "investment-research"
    assert "Investment Research Skill" in str(observation["data"]["content"])


def test_tool_registry_macro_tool_does_not_require_symbol() -> None:
    observation = ToolRegistry().run_tool("get_macro", {"region": "US"})

    assert observation["success"] is True
    assert observation["data"]["region"] == "US"


def test_tool_registry_todo_update_validates_single_in_progress() -> None:
    registry = ToolRegistry()

    rejected = registry.run_tool(
        "todo_update",
        {
            "steps": [
                {"id": "1", "text": "Read quote", "status": "in_progress"},
                {"id": "2", "text": "Read risk", "status": "in_progress"},
            ],
        },
    )
    assert rejected["success"] is False

    accepted = registry.run_tool(
        "todo_update",
        {
            "symbol": "AAPL",
            "steps": [
                {"id": "1", "text": "Read quote", "status": "completed"},
                {"id": "2", "text": "Read risk", "status": "in_progress"},
            ],
        },
    )
    assert accepted["success"] is True
    assert accepted["data"]["steps"][1]["status"] == "in_progress"


def test_react_runtime_exposes_skills_and_compacts_previous_steps() -> None:
    provider = RecordingLLMProvider()

    result = ReActRuntime(llm_provider=provider).run(
        "AAPL",
        question="Use the right skill and summarize context.",
        max_steps=2,
    )

    assert result.final_answer == "AAPL context reviewed."
    assert len(provider.messages_by_call) == 2
    second_user_payload = json.loads(provider.messages_by_call[1][1].content)
    assert "investment-research" in second_user_payload["available_skills"]
    assert any(
        tool["name"] == "load_skill"
        for tool in second_user_payload["tool_manifest"]
    )
    previous_step = second_user_payload["previous_steps"][0]
    assert previous_step["compacted"] is True
    assert previous_step["observation"]["data"]["keys"]
    assert "fundamentals" not in previous_step["observation"]["data"]
