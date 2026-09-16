"""Agent domain model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from agentir.domain.guard import GuardSpec
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.memory import MemorySpec
from agentir.domain.model import ModelSpec
from agentir.domain.output import OutputSpec
from agentir.domain.policy import ExecutionPolicy
from agentir.domain.provenance import SourceProvenance
from agentir.domain.skill import SkillSpec
from agentir.domain.state import StateSpec
from agentir.domain.tool import ToolSpec


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Canonical specification of an autonomous or task-oriented AI agent."""

    id: str
    name: str
    model: ModelSpec
    instructions: InstructionsSpec
    description: str = ""
    tools: Sequence[ToolSpec] = field(default_factory=tuple)
    skills: Sequence[SkillSpec] = field(default_factory=tuple)
    handoffs: Sequence[HandoffSpec] = field(default_factory=tuple)
    memory: MemorySpec | None = None
    state: StateSpec | None = None
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    output: OutputSpec | None = None
    guards: Sequence[GuardSpec] = field(default_factory=tuple)
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: SourceProvenance | None = None

    def get_tool(self, tool_id: str) -> ToolSpec | None:
        """Find an assigned tool by its ID."""
        for t in self.tools:
            if t.id == tool_id:
                return t
        return None
