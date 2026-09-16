"""Unit tests for the AgentIR migration compiler."""

import tempfile
from pathlib import Path

import pytest

from agentir.adapters.registry import get_adapter
from agentir.compiler.pipeline import compile_migration, plan_migration
from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.exceptions import CompatibilityError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.workflow import WorkflowSpec

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_plan_migration_compatible() -> None:
    adapter = get_adapter("langgraph")
    fixture_path = FIXTURES_DIR / "langgraph" / "sample_graph.yaml"
    manifest = adapter.import_manifest(fixture_path)

    plan = plan_migration(manifest, "langgraph")
    assert plan.can_proceed is True
    assert len(plan.blocked_reasons) == 0


def test_compile_migration_success() -> None:
    adapter = get_adapter("agno")
    fixture_path = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    manifest = adapter.import_manifest(fixture_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        res = compile_migration(manifest, "agno", tmp_dir)
        assert res.success is True
        assert res.report_path is not None
        assert res.report_path.is_file()
        assert res.report_json_path is not None
        assert res.report_json_path.is_file()

        report_content = res.report_path.read_text(encoding="utf-8")
        assert "AgentIR Migration Audit Report" in report_content
        assert "Capabilities Summary" in report_content


def test_compile_migration_blocked_incompatible() -> None:
    # A cyclic graph with state checkpointing cannot be migrated to OpenAI Agents without force
    agent = AgentSpec(
        id="worker",
        name="Worker",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Do work"),
    )
    workflow = WorkflowSpec(
        id="cyclic_wf",
        name="Cyclic Workflow",
        entry_node_id="n1",
        finish_node_ids=("END",),
        nodes=(
            NodeSpec(id="n1", type="agent", name="Node 1", agent_id="worker"),
            NodeSpec(id="n2", type="agent", name="Node 2", agent_id="worker"),
        ),
        edges=(
            EdgeSpec(
                source_node_id="n1",
                is_conditional=True,
                path_map={"loop": "n2", "exit": "END"},
            ),
            EdgeSpec(source_node_id="n2", target_node_id="n1"),
        ),
    )
    manifest = AgentIRManifest(name="Graph App", agents=(agent,), workflows=(workflow,))

    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(CompatibilityError) as exc_info:
            compile_migration(manifest, "openai_agents", tmp_dir, force=False)
        assert "conditional_edges" in str(exc_info.value)

        # But with force=True, it succeeds and records the degraded semantics in the report
        res_forced = compile_migration(manifest, "openai_agents", tmp_dir, force=True)
        assert res_forced.success is True
        assert res_forced.report_path is not None
        report_text = res_forced.report_path.read_text(encoding="utf-8")
        assert "conditional_edges" in report_text
