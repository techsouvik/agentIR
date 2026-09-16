"""Golden file tests for generated adapter artifacts."""

import tempfile
from pathlib import Path

from agentir.adapters.registry import get_adapter

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_golden_langgraph_export_structure() -> None:
    adapter = get_adapter("langgraph")
    fixture = FIXTURES_DIR / "langgraph" / "sample_graph.yaml"
    manifest = adapter.import_manifest(fixture)

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        agent_py = Path(tmp_dir) / "agent.py"
        reqs_txt = Path(tmp_dir) / "requirements.txt"

        assert agent_py.is_file()
        assert reqs_txt.is_file()

        code = agent_py.read_text(encoding="utf-8")
        assert "StateGraph(AgentState)" in code
        assert "builder.add_node" in code
        assert "builder.add_conditional_edges" in code
        assert "builder.compile()" in code


def test_golden_agno_export_structure() -> None:
    adapter = get_adapter("agno")
    fixture = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    manifest = adapter.import_manifest(fixture)

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        agent_py = Path(tmp_dir) / "agent.py"
        code = agent_py.read_text(encoding="utf-8")

        assert "from agno.agent import Agent" in code
        assert "from agno.models.openai import OpenAIChat" in code
        assert "agent_support_specialist = Agent(" in code
        assert "agent_billing_specialist = Agent(" in code


def test_golden_openai_agents_export_structure() -> None:
    adapter = get_adapter("openai_agents")
    fixture = FIXTURES_DIR / "openai_agents" / "sample_agents.yaml"
    manifest = adapter.import_manifest(fixture)

    with tempfile.TemporaryDirectory() as tmp_dir:
        generated = adapter.export_manifest(manifest, tmp_dir)
        assert len(generated) >= 2
        agent_py = Path(tmp_dir) / "agent.py"
        code = agent_py.read_text(encoding="utf-8")

        assert "from agents import Agent, Runner" in code
        assert "triage_agent = Agent(" in code
        assert "tech_support_agent = Agent(" in code
        assert "handoffs=[tech_support_agent]" in code
