"""Output specification domain model."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from agentir.domain.tool import ToolInputSchema


@dataclass(frozen=True, slots=True)
class OutputSpec:
    """Structured or textual output requirements for an agent or workflow."""

    format: str = "text"  # "text", "json", "markdown"
    schema_definition: ToolInputSchema | None = None
    pydantic_class_name: str | None = None
    require_valid_json: bool = False
    description: str = ""
    json_schema_dict: Mapping[str, Any] | None = None
