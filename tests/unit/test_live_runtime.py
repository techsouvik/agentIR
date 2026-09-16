"""Unit tests for the LiveRuntime agent harness."""

import json
from typing import Any

import httpx
import pytest

from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import SecurityError
from agentir.domain.guard import GuardSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.runtime.live import LiveRuntime


class _MockResponse:
    def __init__(self, json_data: dict[str, Any], status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self) -> dict[str, Any]:
        return self._json_data


def test_live_runtime_basic_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = AgentSpec(
        id="analyst",
        name="Analyst",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Analyze datasets."),
    )
    manifest = AgentIRManifest(name="Live App", agents=(agent,))

    mock_llm_reply = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am your data analyst.",
                }
            }
        ]
    }

    monkeypatch.setattr(
        httpx.Client,
        "post",
        lambda *_args, **_kwargs: _MockResponse(mock_llm_reply),
    )

    runtime = LiveRuntime(api_key="sk-test-key-mock")
    turn = runtime.chat_turn(manifest, messages=[{"role": "user", "content": "Hi!"}])

    assert turn.assistant_reply == "Hello! I am your data analyst."
    assert len(turn.tool_results) == 0


def test_live_runtime_tool_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = ToolSpec(
        id="calc",
        name="calc",
        description="Calculate math",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="expr", type="string"),)
        ),
    )
    agent = AgentSpec(
        id="math_bot",
        name="Math Bot",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Math helper."),
        tools=(tool,),
    )
    manifest = AgentIRManifest(name="Math App", agents=(agent,))

    # First call requests tool execution; second call gives final answer
    tool_call_reply = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "calc",
                                "arguments": '{"expr": "2 + 2"}',
                            },
                        }
                    ],
                }
            }
        ]
    }
    final_reply = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "The result is 4.",
                }
            }
        ]
    }

    call_count = 0

    def mock_post(*_args: Any, **_kwargs: Any) -> _MockResponse:
        nonlocal call_count
        call_count += 1
        return _MockResponse(tool_call_reply if call_count == 1 else final_reply)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    runtime = LiveRuntime(
        api_key="sk-test-key-mock",
        tool_executor=lambda _tool, _args: "4",
    )
    turn = runtime.chat_turn(manifest, messages=[{"role": "user", "content": "What is 2+2?"}])

    assert turn.assistant_reply == "The result is 4."
    assert len(turn.tool_results) == 1
    assert turn.tool_results[0].tool_name == "calc"
    assert turn.tool_results[0].output == "4"


def test_live_runtime_guard_abort() -> None:
    guard = GuardSpec(
        name="ssn_filter",
        stage="input",
        rule_type="regex_pattern",
        pattern_or_rule=r"\b\d{3}-\d{2}-\d{4}\b",
        action_on_failure="abort",
    )
    agent = AgentSpec(
        id="guard_bot",
        name="Guard Bot",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Safe bot."),
        guards=(guard,),
    )
    manifest = AgentIRManifest(name="Guard App", agents=(agent,))

    runtime = LiveRuntime(api_key="sk-test-key-mock")
    with pytest.raises(SecurityError) as exc_info:
        runtime.chat_turn(manifest, messages=[{"role": "user", "content": "My SSN is 000-12-3456"}])
    assert "blocked by guard" in str(exc_info.value).lower()


def test_live_runtime_gemini_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    """LiveRuntime must auto-resolve Google Gemini base_url and GEMINI_API_KEY."""
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyMockGeminiKey123")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Inferred from model_id
    runtime = LiveRuntime(model_id="gemini-1.5-pro")
    assert runtime.provider == "gemini"
    assert "generativelanguage.googleapis.com" in runtime.base_url
    assert runtime.api_key == "AIzaSyMockGeminiKey123"

    # Inferred from provider hint "google"
    runtime_google = LiveRuntime(provider="google")
    assert runtime_google.provider == "gemini"
    assert "generativelanguage.googleapis.com" in runtime_google.base_url


def test_live_runtime_gemini_chat_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test full chat turn against simulated Gemini endpoint."""
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyMockGeminiKey123")

    mock_gemini_reply = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello from Gemini 1.5 Flash!",
                }
            }
        ]
    }

    captured_url = ""
    captured_headers: dict[str, str] = {}

    def mock_gemini_post(
        _self: Any, url: str, headers: dict[str, str] | None = None, **_kwargs: Any
    ) -> _MockResponse:
        nonlocal captured_url, captured_headers
        captured_url = str(url)
        captured_headers = dict(headers or {})
        return _MockResponse(mock_gemini_reply)

    monkeypatch.setattr(httpx.Client, "post", mock_gemini_post)

    agent = AgentSpec(
        id="gemini_bot",
        name="Gemini Bot",
        model=ModelSpec(provider="gemini", model_id="gemini-1.5-flash"),
        instructions=InstructionsSpec(system_prompt="You are powered by Gemini."),
    )
    manifest = AgentIRManifest(name="Gemini App", agents=(agent,))

    runtime = LiveRuntime(provider="gemini")
    turn = runtime.chat_turn(manifest, messages=[{"role": "user", "content": "Hi Gemini"}])

    assert turn.assistant_reply == "Hello from Gemini 1.5 Flash!"
    assert "generativelanguage.googleapis.com" in captured_url
    assert captured_headers.get("Authorization") == "Bearer AIzaSyMockGeminiKey123"
