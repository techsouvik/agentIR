"""Unit tests for deterministic compiler optimization passes."""

from agentir.compiler.passes import (
    DeadNodeEliminationPass,
    LoopInvariantPass,
    ToolSchemaNormalizationPass,
    create_default_pass_pipeline,
)
from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec
from agentir.schema.canonical import compute_canonical_hash


def test_dead_node_elimination_pass() -> None:
    """Unreachable orphan nodes and dead edges must be pruned."""
    nodes = (
        NodeSpec(id="start", type="agent", name="Start"),
        NodeSpec(id="process", type="agent", name="Process"),
        NodeSpec(id="orphan_dead_node", type="agent", name="Dead Orphan"),
    )
    edges = (
        EdgeSpec(source_node_id="start", target_node_id="process"),
        EdgeSpec(source_node_id="process", target_node_id="END"),
        EdgeSpec(source_node_id="orphan_dead_node", target_node_id="process"),
    )
    wf = WorkflowSpec(
        id="wf_with_dead_code",
        name="Dead Code WF",
        entry_node_id="start",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
    )
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Task"),
    )
    manifest = AgentIRManifest(name="Optimization Test", agents=(agent,), workflows=(wf,))

    pass_obj = DeadNodeEliminationPass()
    optimized, res = pass_obj.run(manifest)

    assert res.mutations_count > 0
    optimized_node_ids = {n.id for n in optimized.workflows[0].nodes}
    assert "start" in optimized_node_ids
    assert "process" in optimized_node_ids
    assert "orphan_dead_node" not in optimized_node_ids


def test_tool_schema_normalization_pass() -> None:
    """Tool schemas with empty descriptions or phantom required fields must be normalized."""
    tool = ToolSpec(
        id="raw_tool",
        name="Raw Tool",
        description="Tool description",
        input_schema=ToolInputSchema(
            properties=(
                ToolParameterProperty(name="field_a", type="UNKNOWN_TYPE", description=""),
            ),
            required=("field_a", "ghost_nonexistent_field"),
        ),
    )
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Task"),
        tools=(tool,),
    )
    manifest = AgentIRManifest(name="Tool Norm Test", agents=(agent,))

    pass_obj = ToolSchemaNormalizationPass()
    optimized, res = pass_obj.run(manifest)

    assert res.mutations_count > 0
    norm_tool = optimized.agents[0].tools[0]
    # Type normalized to string
    assert norm_tool.input_schema.properties[0].type == "string"
    # Empty description filled with default
    assert norm_tool.input_schema.properties[0].description != ""
    # Ghost field pruned from required
    assert "ghost_nonexistent_field" not in norm_tool.input_schema.required


def test_loop_invariant_pass_classification() -> None:
    """Classifies DAG vs Cyclic workflows."""
    wf_dag = WorkflowSpec(
        id="dag_flow",
        name="DAG Flow",
        entry_node_id="n1",
        finish_node_ids=("END",),
        nodes=(NodeSpec(id="n1", type="agent", name="N1"),),
        edges=(EdgeSpec(source_node_id="n1", target_node_id="END"),),
    )
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Task"),
    )
    manifest = AgentIRManifest(name="DAG App", agents=(agent,), workflows=(wf_dag,))

    pass_obj = LoopInvariantPass()
    optimized, _ = pass_obj.run(manifest)
    assert optimized.workflows[0].metadata.get("topology_class") == "DAG"


def test_pass_pipeline_idempotency() -> None:
    """Running the pipeline twice must produce zero mutations on the second pass."""
    tool = ToolSpec(
        id="t1",
        name="T1",
        description="Tool",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="p1", type="string", description=""),),
            required=("p1",),
        ),
    )
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Task"),
        tools=(tool,),
    )
    manifest = AgentIRManifest(name="Idempotency App", agents=(agent,))

    pipeline = create_default_pass_pipeline()
    pass1_manifest, _ = pipeline.run(manifest)
    pass2_manifest, pass2_results = pipeline.run(pass1_manifest)

    # Idempotent: 0 mutations on second run
    assert sum(r.mutations_count for r in pass2_results) == 0
    assert compute_canonical_hash(pass1_manifest) == compute_canonical_hash(pass2_manifest)
