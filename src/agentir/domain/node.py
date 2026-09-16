"""Workflow node domain model."""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class NodeSpec:
    """A computational or decision node within an AgentIR workflow graph."""

    id: str
    type: str  # "agent", "tool", "router", "passthrough", "custom"
    name: str
    agent_id: str | None = None
    tool_id: str | None = None
    handler_name: str | None = None
    description: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)
