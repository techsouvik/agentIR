"""Unit tests for AgentIR schema, serialization, and canonicalization."""

import pytest

from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AgentIRValidationError, SecurityError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.provenance import SourceProvenance
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.schema.canonical import compute_canonical_hash, to_canonical_dict
from agentir.schema.serializer import (
    deserialize_manifest_from_dict,
    deserialize_manifest_from_json,
    deserialize_manifest_from_yaml,
    serialize_manifest_to_json,
    serialize_manifest_to_yaml,
)


def _build_sample_manifest() -> AgentIRManifest:
    tool_search = ToolSpec(
        id="web_search",
        name="Web Search",
        description="Search current web information",
        input_schema=ToolInputSchema(
            properties=(
                ToolParameterProperty(
                    name="query", type="string", description="Query string", required=True
                ),
                ToolParameterProperty(
                    name="num_results", type="integer", description="Result count", default=5
                ),
            ),
            required=("query",),
        ),
        is_pure=True,
    )
    agent = AgentSpec(
        id="researcher_agent",
        name="Research Analyst",
        model=ModelSpec(provider="openai", model_id="gpt-4o", temperature=0.3),
        instructions=InstructionsSpec(
            system_prompt="You are a thorough research analyst.",
            guidelines=("Be precise", "Cite sources"),
        ),
        tools=(tool_search,),
        provenance=SourceProvenance(
            source_framework="langgraph",
            source_identifier="agent_research",
            imported_at="2026-01-01T00:00:00Z",
        ),
    )
    return AgentIRManifest(
        name="Research System",
        description="A multi-agent research manifest",
        agents=(agent,),
    )


def test_yaml_serialization_round_trip() -> None:
    manifest = _build_sample_manifest()
    yaml_text = serialize_manifest_to_yaml(manifest)
    assert "name: Research System" in yaml_text
    assert "web_search" in yaml_text

    loaded = deserialize_manifest_from_yaml(yaml_text)
    assert loaded.name == manifest.name
    assert len(loaded.agents) == 1
    assert loaded.agents[0].id == "researcher_agent"
    assert loaded.agents[0].tools[0].name == "Web Search"
    prop_names = {p.name for p in loaded.agents[0].tools[0].input_schema.properties}
    assert prop_names == {"query", "num_results"}


def test_json_serialization_round_trip() -> None:
    manifest = _build_sample_manifest()
    json_text = serialize_manifest_to_json(manifest, pretty=True)
    assert '"name": "Research System"' in json_text

    loaded = deserialize_manifest_from_json(json_text)
    assert loaded.name == manifest.name
    assert loaded.agents[0].model.model_id == "gpt-4o"


def test_canonical_hash_invariance_under_field_order() -> None:
    manifest1 = _build_sample_manifest()
    hash1 = compute_canonical_hash(manifest1)

    # Reconstruct raw dict with completely reversed key ordering
    d = to_canonical_dict(manifest1)
    reordered_dict = dict(reversed(list(d.items())))
    hash2 = compute_canonical_hash(reordered_dict)
    assert hash1 == hash2


def test_canonical_hash_ignores_ephemeral_imported_at() -> None:
    manifest1 = _build_sample_manifest()
    tool = manifest1.agents[0].tools[0]
    agent2 = AgentSpec(
        id="researcher_agent",
        name="Research Analyst",
        model=ModelSpec(provider="openai", model_id="gpt-4o", temperature=0.3),
        instructions=InstructionsSpec(
            system_prompt="You are a thorough research analyst.",
            guidelines=("Be precise", "Cite sources"),
        ),
        tools=(tool,),
        provenance=SourceProvenance(
            source_framework="langgraph",
            source_identifier="agent_research",
            imported_at="2026-09-16T12:34:56Z",  # Different timestamp
        ),
    )
    manifest2 = AgentIRManifest(
        name="Research System",
        description="A multi-agent research manifest",
        agents=(agent2,),
    )

    assert compute_canonical_hash(manifest1) == compute_canonical_hash(manifest2)


def test_malformed_yaml_rejected() -> None:
    invalid_yaml = "name: Broken\nagents: [unterminated list"
    with pytest.raises(AgentIRValidationError) as exc:
        deserialize_manifest_from_yaml(invalid_yaml)
    assert "Invalid YAML" in str(exc.value)


def test_missing_required_fields_rejected() -> None:
    invalid_data = {"description": "No name provided"}
    with pytest.raises(AgentIRValidationError) as exc:
        deserialize_manifest_from_dict(invalid_data)
    assert "error(s) found" in str(exc.value)


def test_security_max_size_rejection() -> None:
    huge_yaml = "name: " + ("A" * (11 * 1024 * 1024))
    with pytest.raises(SecurityError):
        deserialize_manifest_from_yaml(huge_yaml)
