"""Property-based tests for AgentIR canonicalization, hashing, and serialization invariants."""

import random

from hypothesis import given
from hypothesis import strategies as st

from agentir.analysis.diff import DiffCategory, compare_manifests
from agentir.domain.agent import AgentSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.schema.canonical import compute_canonical_hash
from agentir.schema.serializer import (
    deserialize_manifest_from_yaml,
    serialize_manifest_to_yaml,
)

# Text strategy constrained to safe identifiers
identifier_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=30,
)


@given(
    name=identifier_st,
    model_id=identifier_st,
    prompt=st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs")),
        min_size=1,
        max_size=200,
    ),
    temperature=st.floats(min_value=0.0, max_value=2.0),
)
def test_property_serialization_round_trip(
    name: str, model_id: str, prompt: str, temperature: float
) -> None:
    """Every generated valid manifest must serialize to YAML and deserialize identically."""
    # YAML 1.2 spec normalizes line breaks (\r, \r\n -> \n)
    normalized_prompt = prompt.replace("\r\n", "\n").replace("\r", "\n")

    agent = AgentSpec(
        id=f"agent_{name}",
        name=name,
        model=ModelSpec(provider="openai", model_id=model_id, temperature=round(temperature, 2)),
        instructions=InstructionsSpec(system_prompt=normalized_prompt),
    )
    manifest = AgentIRManifest(name=name, agents=(agent,))

    yaml_str = serialize_manifest_to_yaml(manifest)
    recovered = deserialize_manifest_from_yaml(yaml_str)

    assert recovered.name == manifest.name
    assert len(recovered.agents) == 1
    assert recovered.agents[0].id == manifest.agents[0].id
    assert (
        recovered.agents[0].instructions.system_prompt
        == manifest.agents[0].instructions.system_prompt
    )
    assert compute_canonical_hash(manifest) == compute_canonical_hash(recovered)


@given(
    tool_names=st.lists(identifier_st, min_size=1, max_size=6, unique=True),
)
def test_property_tool_ordering_invariance(tool_names: list[str]) -> None:
    """Canonical hash must be strictly invariant under arbitrary permutations of tools."""
    tools = [
        ToolSpec(
            id=f"tool_{t}",
            name=t,
            description=f"Description of {t}",
            input_schema=ToolInputSchema(
                properties=(ToolParameterProperty(name="arg1", type="string"),)
            ),
        )
        for t in tool_names
    ]

    agent1 = AgentSpec(
        id="agent_x",
        name="Permutation Test Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Test agent"),
        tools=tuple(tools),
    )
    manifest1 = AgentIRManifest(name="Manifest1", agents=(agent1,))
    hash1 = compute_canonical_hash(manifest1)

    # Shuffle tools
    shuffled_tools = list(tools)
    random.seed(42)
    random.shuffle(shuffled_tools)

    agent2 = AgentSpec(
        id="agent_x",
        name="Permutation Test Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Test agent"),
        tools=tuple(shuffled_tools),
    )
    manifest2 = AgentIRManifest(name="Manifest1", agents=(agent2,))
    hash2 = compute_canonical_hash(manifest2)

    assert hash1 == hash2


@given(
    manifest_name=identifier_st,
)
def test_property_diff_identity_reflexivity(manifest_name: str) -> None:
    """Comparing any manifest against itself must always yield EQUIVALENT."""
    agent = AgentSpec(
        id="reflexive_agent",
        name="Reflexive Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(system_prompt="Prompt"),
    )
    manifest = AgentIRManifest(name=manifest_name, agents=(agent,))
    report = compare_manifests(manifest, manifest)

    assert report.is_equivalent is True
    assert report.overall_category == DiffCategory.EQUIVALENT
    assert len(report.entries) == 0
