from app.services.agents.react_runtime import ReActRuntime
from app.services.agents.tool_registry import ToolRegistry


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
