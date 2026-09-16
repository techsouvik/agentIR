"""Unit tests for AgentIR pure domain models."""

import pytest

from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.exceptions import AgentIRValidationError, GraphValidationError
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.workflow import WorkflowSpec


def test_agent_creation() -> None:
    agent = AgentSpec(
        id="analyst_1",
        name="Data Analyst",
        model=ModelSpec(provider="openai", model_id="gpt-4o", temperature=0.2),
        instructions=InstructionsSpec(system_prompt="You analyze datasets rigorously."),
    )
    assert agent.id == "analyst_1"
    assert agent.name == "Data Analyst"
    assert agent.model.provider == "openai"
    assert agent.model.temperature == 0.2
    assert agent.instructions.system_prompt == "You analyze datasets rigorously."


def test_workflow_topology_validation_success() -> None:
    nodes = (
        NodeSpec(id="start_node", type="agent", name="Start Agent", agent_id="agent_1"),
        NodeSpec(id="process_node", type="tool", name="Tool Runner", tool_id="tool_1"),
    )
    edges = (
        EdgeSpec(source_node_id="start_node", target_node_id="process_node"),
        EdgeSpec(source_node_id="process_node", target_node_id="END"),
    )
    wf = WorkflowSpec(
        id="data_pipeline",
        name="Data Pipeline Workflow",
        entry_node_id="start_node",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
    )
    wf.validate_topology()
    assert wf.get_node("start_node") is not None
    assert len(wf.outgoing_edges("start_node")) == 1


def test_workflow_topology_invalid_entry_node() -> None:
    wf = WorkflowSpec(
        id="broken_wf",
        name="Broken",
        entry_node_id="missing_node",
        nodes=(NodeSpec(id="valid_node", type="agent", name="Valid"),),
    )
    with pytest.raises(GraphValidationError) as exc_info:
        wf.validate_topology()
    assert "missing_node" in str(exc_info.value)


def test_workflow_topology_invalid_edge_target() -> None:
    wf = WorkflowSpec(
        id="broken_edge_wf",
        name="Broken Edge",
        entry_node_id="node_a",
        nodes=(NodeSpec(id="node_a", type="agent", name="Node A"),),
        edges=(EdgeSpec(source_node_id="node_a", target_node_id="ghost_node"),),
    )
    with pytest.raises(GraphValidationError) as exc_info:
        wf.validate_topology()
    assert "ghost_node" in str(exc_info.value)


def test_manifest_duplicate_agent_id() -> None:
    a1 = AgentSpec(
        id="dup_id",
        name="First",
        model=ModelSpec(provider="anthropic", model_id="claude-3-5-sonnet"),
        instructions=InstructionsSpec(system_prompt="Prompt 1"),
    )
    a2 = AgentSpec(
        id="dup_id",
        name="Second",
        model=ModelSpec(provider="anthropic", model_id="claude-3-5-sonnet"),
        instructions=InstructionsSpec(system_prompt="Prompt 2"),
    )
    manifest = AgentIRManifest(name="Test Manifest", agents=(a1, a2))
    with pytest.raises(AgentIRValidationError) as exc_info:
        manifest.validate_invariants()
    assert "dup_id" in str(exc_info.value)


def test_manifest_unknown_handoff_target() -> None:
    agent = AgentSpec(
        id="orchestrator",
        name="Orchestrator",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Prompt"),
        handoffs=(HandoffSpec(target_agent_id="nonexistent_agent", description="Delegate"),),
    )
    manifest = AgentIRManifest(name="Test Manifest", agents=(agent,))
    with pytest.raises(AgentIRValidationError) as exc_info:
        manifest.validate_invariants()
    assert "nonexistent_agent" in str(exc_info.value)
