"""Unit tests for the deterministic dry-run runtime engine."""

from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.guard import GuardSpec
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec
from agentir.runtime.engine import DeterministicRuntime


def test_runtime_direct_agent_simulation() -> None:
    tool = ToolSpec(
        id="calc",
        name="Calculator",
        description="Math calculator",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="expr", type="string"),)
        ),
    )
    agent = AgentSpec(
        id="math_agent",
        name="Math Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Solve math problems."),
        tools=(tool,),
    )
    manifest = AgentIRManifest(name="Math App", agents=(agent,))

    runtime = DeterministicRuntime()
    result = runtime.run(
        manifest,
        user_input="What is 42 * 2?",
        mock_tool_responses={"Calculator": "84"},
    )

    assert result.success is True
    assert "Math Agent" in result.final_output
    action_types = [s.action for s in result.steps]
    assert "reasoning" in action_types
    assert "tool_call" in action_types


def test_runtime_input_guard_aborts() -> None:
    guard = GuardSpec(
        name="credit_card_blocker",
        stage="input",
        rule_type="regex_pattern",
        pattern_or_rule=r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
        action_on_failure="abort",
    )
    agent = AgentSpec(
        id="secure_agent",
        name="Secure Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Secure banking."),
        guards=(guard,),
    )
    manifest = AgentIRManifest(name="Secure App", agents=(agent,))

    runtime = DeterministicRuntime()
    result = runtime.run(manifest, user_input="My card is 1234-5678-9012-3456")

    assert result.success is False
    assert "Aborted by input guard" in result.final_output
    assert result.halt_reason is not None
    assert "violation" in result.halt_reason


def test_runtime_handoff_simulation() -> None:
    triage = AgentSpec(
        id="triage",
        name="Triage Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Triage."),
        handoffs=(HandoffSpec(target_agent_id="specialist", description="Delegate"),),
    )
    specialist = AgentSpec(
        id="specialist",
        name="Specialist Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Handle details."),
    )
    manifest = AgentIRManifest(name="Handoff App", agents=(triage, specialist))

    runtime = DeterministicRuntime()
    result = runtime.run(manifest, user_input="Need specialist help.")

    assert result.success is True
    action_types = [s.action for s in result.steps]
    assert "handoff" in action_types


def test_runtime_workflow_simulation() -> None:
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Work"),
    )
    nodes = (
        NodeSpec(id="step_1", type="agent", name="Step 1", agent_id="worker"),
        NodeSpec(id="step_2", type="agent", name="Step 2", agent_id="worker"),
    )
    edges = (
        EdgeSpec(source_node_id="step_1", target_node_id="step_2"),
        EdgeSpec(source_node_id="step_2", target_node_id="END"),
    )
    wf = WorkflowSpec(
        id="linear_wf",
        name="Linear Workflow",
        entry_node_id="step_1",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
    )
    manifest = AgentIRManifest(name="Workflow App", agents=(agent,), workflows=(wf,))

    runtime = DeterministicRuntime()
    result = runtime.run(manifest, user_input="Run the flow")

    assert result.success is True
    assert len(result.steps) >= 3
    node_ids = [s.node_id for s in result.steps]
    assert "step_1" in node_ids
    assert "step_2" in node_ids
    assert "END" in node_ids
