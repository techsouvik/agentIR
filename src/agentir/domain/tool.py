"""Tool and ToolInputSchema domain models."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolParameterProperty:
    """A parameter property in a tool's JSON Schema input definition."""

    name: str
    type: str
    description: str = ""
    required: bool = False
    default: Any | None = None
    enum_values: Sequence[str] = field(default_factory=tuple)
    items_type: str | None = None


@dataclass(frozen=True, slots=True)
class ToolInputSchema:
    """Declarative JSON Schema specification for tool parameters."""

    type: str = "object"
    properties: Sequence[ToolParameterProperty] = field(default_factory=tuple)
    required: Sequence[str] = field(default_factory=tuple)
    additional_properties: bool = False

    def to_json_schema(self) -> dict[str, Any]:
        """Convert the parameter properties to standard JSON Schema dictionary."""
        props: dict[str, dict[str, Any]] = {}
        for p in self.properties:
            prop_def: dict[str, Any] = {
                "type": p.type,
                "description": p.description,
            }
            if p.default is not None:
                prop_def["default"] = p.default
            if p.enum_values:
                prop_def["enum"] = list(p.enum_values)
            if p.items_type and p.type == "array":
                prop_def["items"] = {"type": p.items_type}
            props[p.name] = prop_def

        schema: dict[str, Any] = {
            "type": self.type,
            "properties": props,
            "required": list(self.required),
            "additionalProperties": self.additional_properties,
        }
        return schema


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Specification of an agent capability tool."""

    id: str
    name: str
    description: str
    input_schema: ToolInputSchema = field(default_factory=ToolInputSchema)
    is_pure: bool = False
    requires_approval: bool = False
    timeout_seconds: float | None = None
    permissions: Sequence[str] = field(default_factory=tuple)
    mcp_server: str | None = None
    mcp_tool_name: str | None = None
    return_direct: bool = False
    handler_module: str | None = None
    handler_callable: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
