"""State and channel specification domain models."""

from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StateChannelSpec:
    """A channel within a state schema, including its type and reducer semantics."""

    key: str
    type_name: str
    reducer: str = "replace"  # "replace", "append", "merge", "custom"
    description: str = ""
    default_value: str | None = None


@dataclass(frozen=True, slots=True)
class StateSpec:
    """State schema specification describing channels and update policies."""

    schema_name: str
    channels: Sequence[StateChannelSpec] = field(default_factory=tuple)
    description: str = ""

    def get_channel(self, key: str) -> StateChannelSpec | None:
        """Lookup a channel by its key."""
        for ch in self.channels:
            if ch.key == key:
                return ch
        return None
