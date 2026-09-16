"""Handoff and agent delegation domain models."""

from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class HandoffSpec:
    """Specification of delegation from one agent to another."""

    target_agent_id: str
    description: str
    condition: str | None = None
    transfer_state_keys: Sequence[str] = field(default_factory=tuple)
    return_to_caller: bool = False
