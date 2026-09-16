"""Instructions domain model."""

from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InstructionsSpec:
    """Encapsulates system instructions, persona definitions, and prompting constraints."""

    system_prompt: str
    persona: str | None = None
    role: str | None = None
    template_variables: Sequence[str] = field(default_factory=tuple)
    guidelines: Sequence[str] = field(default_factory=tuple)
    workspace_context: str | None = None
