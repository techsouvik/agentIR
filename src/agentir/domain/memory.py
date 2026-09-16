"""Memory specification domain model."""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MemorySpec:
    """Specification of agent memory policies and storage mechanisms."""

    memory_type: str = "conversation_buffer"
    max_messages: int | None = 50
    summary_window: int | None = None
    vector_collection: str | None = None
    persist_across_sessions: bool = False
    storage_backend: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
