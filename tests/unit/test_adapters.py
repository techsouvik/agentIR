"""Unit and fixture tests for framework adapters."""

import tempfile
from pathlib import Path

from agentir.adapters.registry import get_adapter, list_registered_adapters

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_registry_lists_all_adapters() -> None:
    adapters = list_registered_adapters()
    assert "langgraph" in adapters
    assert "agno" in adapters
    assert "openai_agents" in adapters
    assert "lyzr" in adapters


def test_langgraph_import_yaml_fixture() -> None:
    adapter = get_adapter("langgraph")
    fixture_path = FIXTURES_DIR / "langgraph" / "sample_graph.yaml"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert manifest.name == "LangGraph Customer Support"
    assert len(manifest.agents) == 1
    assert len(manifest.workflows) == 1

    wf = manifest.workflows[0]
    assert wf.entry_node_id == "triage"
    assert len(wf.nodes) == 2
    assert len(wf.edges) == 2
    assert manifest.provenance is not None
    assert manifest.provenance.source_framework == "langgraph"


def test_langgraph_import_python_ast() -> None:
    adapter = get_adapter("langgraph")
    fixture_path = FIXTURES_DIR / "langgraph" / "sample_graph.py"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert len(manifest.workflows) == 1
    wf = manifest.workflows[0]
    assert wf.entry_node_id == "agent"
    assert len(wf.nodes) == 2
    assert any(e.is_conditional for e in wf.edges)


def test_langgraph_export() -> None:
    adapter = get_adapter("langgraph")
    fixture_path = FIXTURES_DIR / "langgraph" / "sample_graph.yaml"
    manifest = adapter.import_manifest(fixture_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        file_names = {p.name for p in generated}
        assert "agent.py" in file_names
        assert "requirements.txt" in file_names

        content = (Path(tmp_dir) / "agent.py").read_text(encoding="utf-8")
        assert "StateGraph(AgentState)" in content
        assert "builder.compile()" in content


def test_agno_import_yaml_fixture() -> None:
    adapter = get_adapter("agno")
    fixture_path = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert len(manifest.agents) == 2
    assert manifest.agents[0].id == "support_specialist"
    assert len(manifest.agents[0].handoffs) == 1
    assert manifest.agents[0].handoffs[0].target_agent_id == "billing_specialist"


def test_agno_import_python_ast() -> None:
    adapter = get_adapter("agno")
    fixture_path = FIXTURES_DIR / "agno" / "sample_agent.py"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert len(manifest.agents) == 1
    assert manifest.agents[0].name == "Support Specialist"


def test_agno_export() -> None:
    adapter = get_adapter("agno")
    fixture_path = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    manifest = adapter.import_manifest(fixture_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        content = (Path(tmp_dir) / "agent.py").read_text(encoding="utf-8")
        assert "from agno.agent import Agent" in content
        assert "OpenAIChat" in content


def test_openai_agents_import_and_export() -> None:
    adapter = get_adapter("openai_agents")
    fixture_path = FIXTURES_DIR / "openai_agents" / "sample_agents.yaml"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert len(manifest.agents) == 2
    assert manifest.agents[0].id == "triage"
    assert len(manifest.agents[0].guards) == 1

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        content = (Path(tmp_dir) / "agent.py").read_text(encoding="utf-8")
        assert "from agents import Agent, Runner" in content
        assert "triage_agent = Agent(" in content


def test_lyzr_import_and_export() -> None:
    adapter = get_adapter("lyzr")
    fixture_path = FIXTURES_DIR / "lyzr" / "sample_pipeline.yaml"
    assert adapter.can_import(fixture_path)

    manifest = adapter.import_manifest(fixture_path)
    assert len(manifest.agents) == 1
    assert manifest.agents[0].instructions.role == "Senior Financial Analyst"

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        content = (Path(tmp_dir) / "agent.py").read_text(encoding="utf-8")
        assert "LinearSyncPipeline" in content
        assert "lyzr_automata" in content
