"""Unit tests for skills domain and schema models."""

from agentir.domain.agent import AgentSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.skill import SkillExample, SkillResource, SkillSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.schema.canonical import compute_canonical_hash
from agentir.schema.serializer import (
    deserialize_manifest_from_yaml,
    serialize_manifest_to_yaml,
)


def test_skill_definition_and_serialization() -> None:
    tool = ToolSpec(
        id="sql_query",
        name="SQL Query",
        description="Run query",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="query", type="string", required=True),),
            required=("query",),
        ),
    )
    resource = SkillResource(
        name="schema_docs",
        uri="file:///docs/schema.sql",
        description="Postgres DDL schema",
        mime_type="application/sql",
    )
    example = SkillExample(
        user_input="How many users registered today?",
        expected_output="SELECT count(*) FROM users WHERE created_at >= current_date;",
        tool_calls=("sql_query",),
    )
    skill = SkillSpec(
        id="sql_expert",
        name="SQL Expert",
        description="Expert SQL generation and optimization",
        instructions="Always check table relationships before writing joins.",
        tools=(tool,),
        resources=(resource,),
        examples=(example,),
    )
    agent = AgentSpec(
        id="analyst",
        name="Analyst",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="You analyze data."),
        skills=(skill,),
    )
    manifest = AgentIRManifest(name="Skills App", agents=(agent,), shared_skills=(skill,))

    yaml_str = serialize_manifest_to_yaml(manifest)
    assert "sql_expert" in yaml_str
    assert "schema_docs" in yaml_str
    assert "How many users registered today?" in yaml_str

    loaded = deserialize_manifest_from_yaml(yaml_str)
    assert len(loaded.shared_skills) == 1
    assert loaded.shared_skills[0].id == "sql_expert"
    assert len(loaded.agents[0].skills) == 1
    assert loaded.agents[0].skills[0].name == "SQL Expert"
    assert loaded.agents[0].skills[0].resources[0].mime_type == "application/sql"

    # Canonical hash determinism
    assert compute_canonical_hash(manifest) == compute_canonical_hash(loaded)
