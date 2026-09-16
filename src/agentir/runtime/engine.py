"""Minimal deterministic execution runtime for dry-run simulation and verification."""

import re
from dataclasses import dataclass, field
from typing import Any

from agentir.domain.agent import AgentSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.workflow import WorkflowSpec


@dataclass(frozen=True, slots=True)
class ExecutionStep:
    """A recorded trace event during simulated runtime execution."""

    turn: int
    agent_id: str
    action: str  # "guard_check", "reasoning", "tool_call", "handoff", "finish"
    node_id: str | None = None
    input_payload: Any = None
    output_payload: Any = None
    state_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """The structured result of an AgentIR dry-run simulation."""

    success: bool
    final_output: str
    steps: tuple[ExecutionStep, ...] = field(default_factory=tuple)
    final_state: dict[str, Any] = field(default_factory=dict)
    halt_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "final_output": self.final_output,
            "turn_count": len(self.steps),
            "halt_reason": self.halt_reason,
            "final_state": self.final_state,
            "steps": [
                {
                    "turn": s.turn,
                    "agent_id": s.agent_id,
                    "action": s.action,
                    "node_id": s.node_id,
                    "input": s.input_payload,
                    "output": s.output_payload,
                }
                for s in self.steps
            ],
        }


class DeterministicRuntime:
    """Executes deterministic offline simulations of AgentIR systems without external LLMs."""

    def run(
        self,
        manifest: AgentIRManifest,
        user_input: str,
        max_turns: int = 10,
        mock_tool_responses: dict[str, Any] | None = None,
    ) -> SimulationResult:
        """Execute a deterministic simulation run."""
        steps: list[ExecutionStep] = []
        state: dict[str, Any] = {"messages": [{"role": "user", "content": user_input}]}
        mock_responses = mock_tool_responses or {}

        if not manifest.agents:
            return SimulationResult(
                success=False,
                final_output="",
                halt_reason="Manifest has no declared agents.",
            )

        current_agent: AgentSpec = manifest.agents[0]

        # 1. Evaluate input guards on initial turn
        for guard in current_agent.guards:
            if guard.stage == "input" and guard.rule_type == "regex_pattern":
                pattern = re.compile(guard.pattern_or_rule, re.IGNORECASE)
                if pattern.search(user_input):
                    step = ExecutionStep(
                        turn=1,
                        agent_id=current_agent.id,
                        action="guard_check",
                        input_payload=user_input,
                        output_payload=(
                            f"Guard '{guard.name}' triggered failure action: "
                            f"{guard.action_on_failure}"
                        ),
                        state_snapshot=dict(state),
                    )
                    steps.append(step)
                    if guard.action_on_failure == "abort":
                        return SimulationResult(
                            success=False,
                            final_output=f"Aborted by input guard '{guard.name}'.",
                            steps=tuple(steps),
                            final_state=state,
                            halt_reason=f"Guard '{guard.name}' violation.",
                        )

        # 2. If workflow graph exists, simulate graph execution
        if manifest.workflows:
            return self._simulate_workflow(
                workflow=manifest.workflows[0],
                user_input=user_input,
                initial_state=state,
                initial_steps=steps,
                max_turns=max_turns,
                mock_responses=mock_responses,
            )

        # 3. Direct agent / handoff simulation
        turn = len(steps) + 1
        while turn <= max_turns:
            # Model turn step
            step_resp = f"Simulated response from {current_agent.name} for: {user_input[:40]}"
            steps.append(
                ExecutionStep(
                    turn=turn,
                    agent_id=current_agent.id,
                    action="reasoning",
                    input_payload=user_input,
                    output_payload=step_resp,
                    state_snapshot=dict(state),
                )
            )

            # Check if tools should execute
            if current_agent.tools:
                tool = current_agent.tools[0]
                tool_output = mock_responses.get(
                    tool.name, mock_responses.get(tool.id, f"Mock output for {tool.name}")
                )
                steps.append(
                    ExecutionStep(
                        turn=turn,
                        agent_id=current_agent.id,
                        action="tool_call",
                        input_payload={"tool": tool.name},
                        output_payload=tool_output,
                        state_snapshot=dict(state),
                    )
                )

            # Check handoffs
            if current_agent.handoffs:
                target_id = current_agent.handoffs[0].target_agent_id
                target_agent = manifest.get_agent(target_id)
                if target_agent:
                    steps.append(
                        ExecutionStep(
                            turn=turn,
                            agent_id=current_agent.id,
                            action="handoff",
                            input_payload={"target": target_id},
                            output_payload=f"Delegated to {target_agent.name}",
                            state_snapshot=dict(state),
                        )
                    )
                    current_agent = target_agent

            # Simulated conclusion
            state["messages"].append({"role": "assistant", "content": step_resp})
            return SimulationResult(
                success=True,
                final_output=step_resp,
                steps=tuple(steps),
                final_state=state,
            )

        return SimulationResult(
            success=False,
            final_output="",
            steps=tuple(steps),
            final_state=state,
            halt_reason=f"Exceeded max turns ({max_turns}).",
        )

    def _simulate_workflow(
        self,
        workflow: WorkflowSpec,
        user_input: str,
        initial_state: dict[str, Any],
        initial_steps: list[ExecutionStep],
        max_turns: int,
        mock_responses: dict[str, Any],
    ) -> SimulationResult:
        steps = list(initial_steps)
        state = dict(initial_state)
        current_node_id = workflow.entry_node_id
        turn = len(steps) + 1

        while turn <= max_turns:
            node = workflow.get_node(current_node_id)
            if not node:
                break

            agent_id = node.agent_id or "graph_runner"
            node_output = f"Node '{node.name}' executed."
            if node.type == "tool" and node.tool_id:
                node_output = mock_responses.get(node.tool_id, f"Mock result for {node.tool_id}")

            steps.append(
                ExecutionStep(
                    turn=turn,
                    node_id=node.id,
                    agent_id=agent_id,
                    action="tool_call" if node.type == "tool" else "reasoning",
                    input_payload=user_input,
                    output_payload=node_output,
                    state_snapshot=dict(state),
                )
            )

            # Route edges
            edges = workflow.outgoing_edges(current_node_id)
            if not edges:
                break

            edge = edges[0]
            if edge.is_conditional:
                # Pick first branch
                next_target = list(edge.path_map.values())[0] if edge.path_map else "END"
            else:
                next_target = edge.target_node_id or "END"

            if next_target == "END" or next_target in workflow.finish_node_ids:
                steps.append(
                    ExecutionStep(
                        turn=turn,
                        node_id="END",
                        agent_id=agent_id,
                        action="finish",
                        output_payload="Workflow completed successfully.",
                        state_snapshot=dict(state),
                    )
                )
                return SimulationResult(
                    success=True,
                    final_output=node_output,
                    steps=tuple(steps),
                    final_state=state,
                )

            current_node_id = next_target
            turn += 1

        return SimulationResult(
            success=True,
            final_output="Completed simulation.",
            steps=tuple(steps),
            final_state=state,
        )
