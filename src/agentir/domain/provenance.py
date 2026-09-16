"""Source provenance tracking for imported and exported agents."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    """Records the origin framework, version, and location of an agent definition.

    Provenance tracks where an entity originated without affecting its semantic equivalence
    in canonical diffs.
    """

    source_framework: str
    source_identifier: str
    source_file: str | None = None
    framework_version: str | None = None
    adapter_version: str | None = None
    imported_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    metadata: Mapping[str, str] = field(default_factory=dict)
