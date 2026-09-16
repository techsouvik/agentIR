"""Unit tests for CrewAI adapter."""

import tempfile
from pathlib import Path

from agentir.adapters.registry import get_adapter


def test_crewai_import_and_export() -> None:
    adapter = get_adapter("crewai")
    assert adapter.framework_name == "crewai"

    crew_yaml = """
framework: crewai
name: Marketing Campaign Crew
agents:
  - id: researcher
    name: Market Researcher
    role: Senior Market Research Analyst
    goal: Identify top consumer trends in AI tools
    backstory: Veteran tech analyst with 10 years experience.
    model:
      provider: openai
      model_id: gpt-4o
    tools:
      - name: search_trends
        description: Search current market trend data
  - id: copywriter
    name: Lead Copywriter
    role: Creative Director
    goal: Craft viral marketing ad copy
    backstory: Award-winning copywriter.
tasks:
  - description: Conduct industry search on AI developer tooling
    agent_id: researcher
  - description: Write three high-conversion landing page headlines
    agent_id: copywriter
"""

    with tempfile.TemporaryDirectory() as tmp_dir:
        src_file = Path(tmp_dir) / "crew.yaml"
        src_file.write_text(crew_yaml, encoding="utf-8")

        assert adapter.can_import(src_file)
        manifest = adapter.import_manifest(src_file)

        assert manifest.name == "Marketing Campaign Crew"
        assert len(manifest.agents) == 2
        assert manifest.agents[0].id == "researcher"
        assert len(manifest.workflows) == 1
        assert len(manifest.workflows[0].nodes) == 2

        out_dir = Path(tmp_dir) / "exported_crewai"
        files = adapter.export_manifest(manifest, out_dir)
        file_names = {f.name for f in files}
        assert "agent.py" in file_names
        assert "requirements.txt" in file_names

        code = (out_dir / "agent.py").read_text(encoding="utf-8")
        assert "from crewai import Agent, Task, Crew, Process" in code
        assert "Senior Market Research Analyst" in code
        assert "Creative Director" in code
        assert "crew = Crew(" in code
