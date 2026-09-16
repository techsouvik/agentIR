"""Model specification domain model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Specification of an LLM or reasoning model binding.

    Captures model identity and generation hyperparameters in a framework-neutral format.
    """

    provider: str
    model_id: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop_sequences: Sequence[str] = field(default_factory=tuple)
    reasoning_effort: str | None = None
    timeout_seconds: float | None = None
    configuration: Mapping[str, str] = field(default_factory=dict)
