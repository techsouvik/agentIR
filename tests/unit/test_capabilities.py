"""Unit tests for capability extraction and compatibility analysis."""

import pytest

from agentir.capabilities.analyzer import (
    analyze_compatibility,
    extract_required_capabilities,
)
from agentir.capabilities.status import SemanticLossRisk
from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.exceptions import UnsupportedCapabilityError
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.memory import MemorySpec
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.policy import ExecutionPolicy
from agentir.domain.state import StateChannelSpec, StateSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec


def _create_graph_manifest() -> AgentIRManifest:
    """Create a complex manifest with cyclic conditional edges and checkpoints."""
    state = StateSpec(
        schema_name="WorkflowState",
        channels=(
            StateChannelSpec(key="messages", type_name="list", reducer="append"),
            StateChannelSpec(key="counter", type_name="int", reducer="replace"),
        ),
    )
    tool = ToolSpec(
        id="calc",
        name="Calculator",
        description="Math calculator",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="expr", type="string", required=True),),
            required=("expr",),
        ),
    )
    agent = AgentSpec(
        id="worker",
        name="Worker Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Solve math problems."),
        tools=(tool,),
        memory=MemorySpec(memory_type="conversation_buffer"),
        execution_policy=ExecutionPolicy(requires_human_approval=True, streaming=True),
    )
    nodes = (
        NodeSpec(id="agent_node", type="agent", name="Agent Step", agent_id="worker"),
        NodeSpec(id="tool_node", type="tool", name="Tool Step", tool_id="calc"),
    )
    edges = (
        EdgeSpec(
            source_node_id="agent_node",
            is_conditional=True,
            path_map={"call_tool": "tool_node", "done": "END"},
        ),
        EdgeSpec(source_node_id="tool_node", target_node_id="agent_node"),
    )
    workflow = WorkflowSpec(
        id="math_loop",
        name="Math Loop Graph",
        entry_node_id="agent_node",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
        state=state,
        execution_policy=ExecutionPolicy(interrupt_before_nodes=("tool_node",)),
    )
    return AgentIRManifest(
        name="Math Graph System",
        agents=(agent,),
        workflows=(workflow,),
    )


def test_extract_required_capabilities() -> None:
    manifest = _create_graph_manifest()
    caps = extract_required_capabilities(manifest)

    assert "model_calling" in caps
    assert "tool_calling" in caps
    assert "memory" in caps
    assert "persistent_state" in caps
    assert "checkpointing" in caps
    assert "conditional_edges" in caps
    assert "routing" in caps
    assert "human_approval" in caps
    assert "interrupts" in caps
    assert "streaming" in caps


def test_langgraph_compatibility_full() -> None:
    manifest = _create_graph_manifest()
    report = analyze_compatibility(manifest, "langgraph")

    assert report.is_compatible is True
    assert report.score >= 90.0
    assert report.target_framework == "langgraph"

    native_ids = {c.capability_id for c in report.native}
    assert "conditional_edges" in native_ids
    assert "checkpointing" in native_ids
    assert "interrupts" in native_ids
    assert len(report.unsupported) == 0


def test_openai_agents_incompatibility_with_graph() -> None:
    manifest = _create_graph_manifest()
    report = analyze_compatibility(manifest, "openai_agents")

    # OpenAI Agents SDK does not support conditional edges or graph checkpointing
    assert report.is_compatible is False
    unsupported_ids = {c.capability_id for c in report.unsupported}
    assert "conditional_edges" in unsupported_ids
    assert "checkpointing" in unsupported_ids

    # Find the critical risk
    critical_risks = [
        r for r in report.semantic_loss_risks
        if r.get("risk_level") == SemanticLossRisk.CRITICAL.value
    ]
    assert len(critical_risks) > 0


def test_handoff_agents_openai_compatibility() -> None:
    """A multi-agent handoff manifest without raw graphs should be compatible with OpenAI."""
    a1 = AgentSpec(
        id="triage",
        name="Triage",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Triage requests."),
        handoffs=(HandoffSpec(target_agent_id="specialist", description="Delegate specialist"),),
    )
    a2 = AgentSpec(
        id="specialist",
        name="Specialist",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Handle details."),
    )
    manifest = AgentIRManifest(name="Triage System", agents=(a1, a2))
    report = analyze_compatibility(manifest, "openai_agents")

    assert report.is_compatible is True
    native_ids = {c.capability_id for c in report.native}
    assert "handoff" in native_ids


def test_unknown_framework_raises() -> None:
    manifest = _create_graph_manifest()
    with pytest.raises(UnsupportedCapabilityError) as exc:
        analyze_compatibility(manifest, "nonexistent_framework")
    assert "Available" in str(exc.value)


def test_compatibility_report_to_dict() -> None:
    manifest = _create_graph_manifest()
    report = analyze_compatibility(manifest, "agno")
    data = report.to_dict()

    assert data["target_framework"] == "agno"
    assert "score" in data
    assert "is_compatible" in data
    assert isinstance(data["required_capabilities"], list)
    assert isinstance(data["evidence"], list)
