"""Skill and modular capability domain models."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from agentir.domain.tool import ToolSpec


@dataclass(frozen=True, slots=True)
class SkillResource:
    """A static or dynamic reference resource attached to a skill."""

    name: str
    uri: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass(frozen=True, slots=True)
class SkillExample:
    """Few-shot demonstration example for skill invocation."""

    user_input: str
    expected_output: str
    tool_calls: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SkillSpec:
    """Modular skill package bundling prompt guidelines, tools, resources, and examples.

    Inspired by Hermes Agent, OpenClaw, and Anthropic Skills architectures.
    """

    id: str
    name: str
    description: str
    instructions: str
    tools: Sequence[ToolSpec] = field(default_factory=tuple)
    resources: Sequence[SkillResource] = field(default_factory=tuple)
    examples: Sequence[SkillExample] = field(default_factory=tuple)
    metadata: Mapping[str, str] = field(default_factory=dict)
