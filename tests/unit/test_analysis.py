"""Unit tests for semantic diff and verification engine."""

from agentir.analysis.diff import (
    DiffCategory,
    compare_agents,
    compare_manifests,
)
from agentir.analysis.verification import verify_manifest
from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec


def _sample_agent(
    agent_id: str = "agent_1",
    model_id: str = "gpt-4o",
    prompt: str = "You are a helpful analyst.",
    tools: tuple[ToolSpec, ...] = (),
    metadata: dict[str, str] | None = None,
) -> AgentSpec:
    return AgentSpec(
        id=agent_id,
        name="Test Agent",
        model=ModelSpec(provider="openai", model_id=model_id),
        instructions=InstructionsSpec(system_prompt=prompt),
        tools=tools,
        metadata=metadata or {},
    )


def test_semantic_diff_equivalent() -> None:
    a1 = _sample_agent()
    a2 = _sample_agent()
    report = compare_agents(a1, a2)
    assert report.is_equivalent is True
    assert report.overall_category == DiffCategory.EQUIVALENT


def test_semantic_diff_behavioral_model_change() -> None:
    a1 = _sample_agent(model_id="gpt-4o")
    a2 = _sample_agent(model_id="claude-3-5-sonnet")
    report = compare_agents(a1, a2)
    assert report.is_equivalent is False
    assert report.overall_category == DiffCategory.BEHAVIORAL
    assert any("model_id" in e.path for e in report.entries)


def test_semantic_diff_breaking_tool_removed() -> None:
    tool = ToolSpec(id="search", name="Search", description="Web search")
    a1 = _sample_agent(tools=(tool,))
    a2 = _sample_agent(tools=())
    report = compare_agents(a1, a2)
    assert report.is_equivalent is False
    assert report.overall_category == DiffCategory.BREAKING


def test_semantic_diff_additive_tool_added() -> None:
    tool = ToolSpec(id="search", name="Search", description="Web search")
    a1 = _sample_agent(tools=())
    a2 = _sample_agent(tools=(tool,))
    report = compare_agents(a1, a2)
    assert report.is_equivalent is False
    assert report.overall_category == DiffCategory.ADDITIVE


def test_semantic_diff_metadata_only() -> None:
    m1 = AgentIRManifest(name="System 1", metadata={"version": "1.0"}, agents=(_sample_agent(),))
    m2 = AgentIRManifest(name="System 1", metadata={"version": "1.1"}, agents=(_sample_agent(),))
    report = compare_manifests(m1, m2)
    assert report.is_equivalent is False
    assert report.overall_category == DiffCategory.METADATA_ONLY


def test_verify_manifest_healthy() -> None:
    tool = ToolSpec(
        id="lookup",
        name="Lookup",
        description="Lookup customer details",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="id", type="string", required=True),),
            required=("id",),
        ),
    )
    manifest = AgentIRManifest(
        name="Healthy Manifest",
        agents=(_sample_agent(tools=(tool,)),),
    )
    report = verify_manifest(manifest)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_verify_manifest_secret_leakage_detected() -> None:
    leaked_agent = _sample_agent(
        prompt="Use this sk-proj-1234567890abcdef1234567890 key to call the API."
    )
    manifest = AgentIRManifest(name="Leaky App", agents=(leaked_agent,))
    report = verify_manifest(manifest)
    assert report.is_valid is False
    assert any("secret_detection" in c.name and not c.passed for c in report.checks)


def test_verify_manifest_unreachable_node_warning() -> None:
    agent = _sample_agent()
    nodes = (
        NodeSpec(id="start", type="agent", name="Start", agent_id=agent.id),
        NodeSpec(id="orphan", type="agent", name="Orphan", agent_id=agent.id),
    )
    edges = (EdgeSpec(source_node_id="start", target_node_id="END"),)
    wf = WorkflowSpec(
        id="wf_orphan",
        name="Orphan WF",
        entry_node_id="start",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
    )
    manifest = AgentIRManifest(name="Orphan App", agents=(agent,), workflows=(wf,))
    report = verify_manifest(manifest)
    assert any("workflow_reachability" in c.name and not c.passed for c in report.checks)
    assert any("orphan" in w for w in report.warnings)
