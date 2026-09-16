"""Serialization and deserialization between AgentIR domain models and YAML/JSON."""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AgentIRValidationError, SecurityError
from agentir.domain.manifest import AgentIRManifest
from agentir.schema.canonical import to_canonical_dict
from agentir.schema.models import AgentIRManifestSchema, AgentSpecSchema

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit for untrusted input


class _SafeDumper(yaml.SafeDumper):
    """Safe YAML dumper that preserves deterministic sorting."""


def _dict_representer(dumper: yaml.SafeDumper, data: dict[str, Any]) -> yaml.nodes.MappingNode:
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


_SafeDumper.add_representer(dict, _dict_representer)


def serialize_manifest_to_dict(manifest: AgentIRManifest) -> dict[str, Any]:
    """Serialize a manifest to a raw dictionary."""
    return AgentIRManifestSchema.from_domain(manifest).model_dump(mode="json", exclude_none=True)


def serialize_manifest_to_yaml(manifest: AgentIRManifest, canonical: bool = True) -> str:
    """Serialize an AgentIRManifest to a YAML string."""
    data = to_canonical_dict(manifest) if canonical else serialize_manifest_to_dict(manifest)
    return yaml.dump(
        data,
        Dumper=_SafeDumper,
        default_flow_style=False,
        sort_keys=True,
        allow_unicode=True,
    )


def serialize_manifest_to_json(
    manifest: AgentIRManifest, pretty: bool = True, canonical: bool = True
) -> str:
    """Serialize an AgentIRManifest to a JSON string."""
    data = to_canonical_dict(manifest) if canonical else serialize_manifest_to_dict(manifest)
    indent = 2 if pretty else None
    return json.dumps(
        data,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
    )


def deserialize_manifest_from_dict(data: dict[str, Any]) -> AgentIRManifest:
    """Deserialize an AgentIRManifest from a dictionary with strict validation."""
    if not isinstance(data, dict):
        raise AgentIRValidationError(
            f"Expected manifest document to be a mapping, got {type(data).__name__}"
        )
    try:
        schema = AgentIRManifestSchema.model_validate(data)
        return schema.to_domain()
    except ValidationError as e:
        errors = e.errors()
        formatted_errors = [
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in errors
        ]
        raise AgentIRValidationError(
            f"Failed to validate AgentIR manifest: {len(errors)} error(s) found.",
            {"errors": formatted_errors},
        ) from e


def deserialize_manifest_from_yaml(content: str) -> AgentIRManifest:
    """Safely parse and validate a YAML document into an AgentIRManifest."""
    if len(content.encode("utf-8")) > MAX_DOCUMENT_SIZE_BYTES:
        raise SecurityError(
            f"Input document exceeds maximum allowed size of {MAX_DOCUMENT_SIZE_BYTES} bytes."
        )
    try:
        raw_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise AgentIRValidationError(f"Invalid YAML syntax: {e}") from e

    if not isinstance(raw_data, dict):
        raise AgentIRValidationError(
            f"YAML document root must be an object/mapping, got {type(raw_data).__name__}"
        )

    return deserialize_manifest_from_dict(raw_data)


def deserialize_manifest_from_json(content: str) -> AgentIRManifest:
    """Parse and validate a JSON document into an AgentIRManifest."""
    if len(content.encode("utf-8")) > MAX_DOCUMENT_SIZE_BYTES:
        raise SecurityError(
            f"Input document exceeds maximum allowed size of {MAX_DOCUMENT_SIZE_BYTES} bytes."
        )
    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as e:
        raise AgentIRValidationError(f"Invalid JSON syntax: {e}") from e

    if not isinstance(raw_data, dict):
        raise AgentIRValidationError(
            f"JSON document root must be an object/mapping, got {type(raw_data).__name__}"
        )

    return deserialize_manifest_from_dict(raw_data)


def load_manifest_from_file(file_path: Path | str) -> AgentIRManifest:
    """Load an AgentIRManifest from a YAML or JSON file on disk."""
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"AgentIR manifest file not found: {path}")

    content = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        return deserialize_manifest_from_yaml(content)
    if suffix == ".json":
        return deserialize_manifest_from_json(content)

    # Try YAML first (which is a superset of JSON)
    try:
        return deserialize_manifest_from_yaml(content)
    except AgentIRValidationError:
        return deserialize_manifest_from_json(content)


def serialize_agent_to_dict(agent: AgentSpec) -> dict[str, Any]:
    """Serialize a single AgentSpec to a dictionary."""
    return AgentSpecSchema.from_domain(agent).model_dump(mode="json", exclude_none=True)


def deserialize_agent_from_dict(data: dict[str, Any]) -> AgentSpec:
    """Deserialize a single AgentSpec from a dictionary."""
    try:
        schema = AgentSpecSchema.model_validate(data)
        return schema.to_domain()
    except ValidationError as e:
        errors = e.errors()
        formatted_errors = [
            {
                "loc": list(err.get("loc", [])),
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in errors
        ]
        raise AgentIRValidationError(
            f"Failed to validate AgentSpec: {len(errors)} error(s) found.",
            {"errors": formatted_errors},
        ) from e
