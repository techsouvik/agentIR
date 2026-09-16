"""Live agent harness runtime using standard HTTP foundation model endpoints."""

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import SecurityError
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.tool import ToolSpec


@dataclass
class ToolExecutionResult:
    """The result of a tool execution turn."""

    tool_name: str
    arguments: dict[str, Any]
    output: str
    requires_approval: bool = False
    approved: bool = True


@dataclass
class LiveChatTurn:
    """Outcome of a single conversational turn in the live harness."""

    assistant_reply: str
    tool_results: list[ToolExecutionResult] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)


class LiveRuntime:
    """Live interactive agent harness connecting AgentIR agents to real LLMs."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 60.0,
        tool_executor: Callable[[ToolSpec, dict[str, Any]], str] | None = None,
        approval_hook: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> None:
        self.api_key = (
            api_key
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("AGENTIR_API_KEY")
            or ""
        )
        self.base_url = (
            base_url
            or os.environ.get("OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.tool_executor = tool_executor or self._default_tool_executor
        self.approval_hook = approval_hook or (lambda _name, _args: True)

    def chat_turn(
        self,
        manifest: AgentIRManifest,
        messages: list[dict[str, Any]],
        agent: AgentSpec | None = None,
    ) -> LiveChatTurn:
        """Execute one complete reasoning and tool-calling loop turn."""
        target_agent = agent or (manifest.agents[0] if manifest.agents else None)
        if not target_agent:
            raise ValueError("Manifest has no agents to chat with.")

        # 1. Evaluate input guardrails on the latest user message
        if messages and messages[-1].get("role") == "user":
            user_text = str(messages[-1].get("content", ""))
            for guard in target_agent.guards:
                if guard.stage == "input" and guard.rule_type == "regex_pattern":
                    pattern = re.compile(guard.pattern_or_rule, re.IGNORECASE)
                    if pattern.search(user_text) and guard.action_on_failure == "abort":
                        msg = f"Message blocked by guard '{guard.name}': {guard.description}"
                        raise SecurityError(msg)

        # 2. Build full prompt payload
        system_content = self._build_system_prompt(target_agent)
        full_messages = [{"role": "system", "content": system_content}, *messages]

        # 3. Format tools in standard OpenAI function calling format
        tools_payload = self._format_tools_payload(target_agent)

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        model_id = target_agent.model.model_id or "gpt-4o"
        temperature = (
            target_agent.model.temperature
            if target_agent.model.temperature is not None
            else 0.7
        )

        body: dict[str, Any] = {
            "model": model_id,
            "messages": full_messages,
            "temperature": temperature,
        }
        if tools_payload:
            body["tools"] = tools_payload

        # 4. Invoke LLM endpoint
        tool_results: list[ToolExecutionResult] = []
        max_tool_iterations = 5

        with httpx.Client(timeout=self.timeout_seconds) as client:
            for _ in range(max_tool_iterations):
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                if resp.status_code != 200:
                    err_msg = f"LLM API request failed with status {resp.status_code}: {resp.text}"
                    raise RuntimeError(err_msg)

                data = resp.json()
                choice = data["choices"][0]
                message = choice["message"]

                # Check if model requested tool calls
                raw_tool_calls = message.get("tool_calls")
                if not raw_tool_calls:
                    final_reply = message.get("content") or ""
                    return LiveChatTurn(
                        assistant_reply=final_reply,
                        tool_results=tool_results,
                        raw_response=data,
                    )

                # Process tool calls
                full_messages.append(message)
                for tc in raw_tool_calls:
                    fn_name = tc["function"]["name"]
                    try:
                        fn_args = json.loads(tc["function"].get("arguments", "{}"))
                    except Exception:
                        fn_args = {}

                    tool_spec = target_agent.get_tool(fn_name) or self._find_tool_by_name(
                        target_agent, fn_name
                    )

                    is_approved = True
                    if tool_spec and tool_spec.requires_approval:
                        is_approved = self.approval_hook(fn_name, fn_args)

                    if not is_approved:
                        out_str = "Error: Tool execution rejected by user."
                    elif tool_spec:
                        out_str = self.tool_executor(tool_spec, fn_args)
                    else:
                        out_str = f"Executed {fn_name}"

                    tool_results.append(
                        ToolExecutionResult(
                            tool_name=fn_name,
                            arguments=fn_args,
                            output=out_str,
                            requires_approval=tool_spec.requires_approval if tool_spec else False,
                            approved=is_approved,
                        )
                    )

                    # Feed tool result back into conversation
                    full_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": fn_name,
                            "content": out_str,
                        }
                    )

                body["messages"] = full_messages

        return LiveChatTurn(
            assistant_reply="Reached maximum tool call iterations.",
            tool_results=tool_results,
        )

    def _build_system_prompt(self, agent: AgentSpec) -> str:
        """Compose instructions, persona, and guidelines into system prompt."""
        parts = [agent.instructions.system_prompt]
        if agent.instructions.role:
            parts.append(f"Your role: {agent.instructions.role}")
        if agent.instructions.persona:
            parts.append(f"Your persona: {agent.instructions.persona}")
        if agent.instructions.guidelines:
            parts.append("Guidelines to strictly observe:")
            for g in agent.instructions.guidelines:
                parts.append(f"- {g}")

        # If skills attached, include skill instructions
        if agent.skills:
            parts.append("\nActive Skills:")
            for skill in agent.skills:
                parts.append(f"Skill '{skill.name}': {skill.instructions}")

        return "\n".join(parts)

    def _format_tools_payload(self, agent: AgentSpec) -> list[dict[str, Any]]:
        """Format agent tools into OpenAI function calling format."""
        all_tools = list(agent.tools)
        for s in agent.skills:
            all_tools.extend(s.tools)

        payload: list[dict[str, Any]] = []
        for t in all_tools:
            fn_name = t.name.lower().replace(" ", "_")
            payload.append(
                {
                    "type": "function",
                    "function": {
                        "name": fn_name,
                        "description": t.description,
                        "parameters": t.input_schema.to_json_schema(),
                    },
                }
            )
        return payload

    def _find_tool_by_name(self, agent: AgentSpec, fn_name: str) -> ToolSpec | None:
        all_tools = list(agent.tools)
        for s in agent.skills:
            all_tools.extend(s.tools)
        for t in all_tools:
            if t.name.lower().replace(" ", "_") == fn_name.lower():
                return t
        return None

    def _default_tool_executor(self, tool: ToolSpec, arguments: dict[str, Any]) -> str:
        """Default tool executor for live turns."""
        if tool.mcp_server:
            return f"[MCP Tool '{tool.name}' on '{tool.mcp_server}'] Result for {arguments}"
        return f"[Executed tool '{tool.name}'] Output with parameters: {arguments}"
