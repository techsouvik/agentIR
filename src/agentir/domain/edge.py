"""Workflow edge domain model."""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EdgeSpec:
    """A direct or conditional transition between workflow nodes."""

    source_node_id: str
    target_node_id: str | None = None
    is_conditional: bool = False
    condition_expression: str | None = None
    router_callable: str | None = None
    path_map: Mapping[str, str] = field(default_factory=dict)
    description: str = ""
