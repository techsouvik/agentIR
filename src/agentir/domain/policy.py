"""Execution policy domain model."""

from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Constraints, limits, and runtime control policies for agent/graph execution."""

    max_turns: int | None = 25
    timeout_seconds: float | None = 300.0
    retry_limit: int = 0
    retry_delay_seconds: float = 1.0
    allow_delegation: bool = True
    requires_human_approval: bool = False
    interrupt_before_nodes: Sequence[str] = field(default_factory=tuple)
    interrupt_after_nodes: Sequence[str] = field(default_factory=tuple)
    parallel_execution: bool = False
    streaming: bool = False
