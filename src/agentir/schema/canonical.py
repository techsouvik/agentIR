"""Deterministic canonicalization and hashing for AgentIR entities."""

import hashlib
import json
from typing import Any

from agentir.domain.agent import AgentSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.workflow import WorkflowSpec
from agentir.schema.models import AgentIRManifestSchema, AgentSpecSchema, WorkflowSpecSchema

# Fields that represent ephemeral metadata and must be excluded from canonical identity
EXCLUDED_HASH_FIELDS = frozenset({"imported_at", "timestamp"})


def _sort_canonical(obj: Any) -> Any:
    """Recursively sort dictionaries by key and normalize values for deterministic output."""
    if isinstance(obj, dict):
        # Exclude non-semantic ephemeral keys
        return {
            k: _sort_canonical(v)
            for k, v in sorted(obj.items())
            if k not in EXCLUDED_HASH_FIELDS
        }
    if isinstance(obj, list):
        return [_sort_canonical(item) for item in obj]
    return obj


def _normalize_manifest_collections(data: dict[str, Any]) -> dict[str, Any]:
    """Sort collection elements by their unique identifiers before canonicalizing."""
    data = dict(data)

    # Sort agents by id
    if "agents" in data and isinstance(data["agents"], list):
        data["agents"] = sorted(
            [_normalize_agent_collections(a) for a in data["agents"]],
            key=lambda x: x.get("id", ""),
        )

    # Sort workflows by id
    if "workflows" in data and isinstance(data["workflows"], list):
        data["workflows"] = sorted(
            [_normalize_workflow_collections(w) for w in data["workflows"]],
            key=lambda x: x.get("id", ""),
        )

    # Sort shared tools by id
    if "shared_tools" in data and isinstance(data["shared_tools"], list):
        data["shared_tools"] = sorted(
            [_normalize_tool_collections(t) for t in data["shared_tools"]],
            key=lambda x: x.get("id", ""),
        )

    # Sort shared skills by id
    if "shared_skills" in data and isinstance(data["shared_skills"], list):
        data["shared_skills"] = sorted(
            data["shared_skills"],
            key=lambda x: x.get("id", ""),
        )

    return data


def _normalize_agent_collections(data: dict[str, Any]) -> dict[str, Any]:
    """Sort collections within an agent dictionary."""
    data = dict(data)
    if "tools" in data and isinstance(data["tools"], list):
        data["tools"] = sorted(
            [_normalize_tool_collections(t) for t in data["tools"]],
            key=lambda x: x.get("id", ""),
        )
    if "skills" in data and isinstance(data["skills"], list):
        data["skills"] = sorted(
            data["skills"],
            key=lambda x: x.get("id", ""),
        )
    if "handoffs" in data and isinstance(data["handoffs"], list):
        data["handoffs"] = sorted(
            data["handoffs"],
            key=lambda x: x.get("target_agent_id", ""),
        )
    if "guards" in data and isinstance(data["guards"], list):
        data["guards"] = sorted(
            data["guards"],
            key=lambda x: x.get("name", ""),
        )
    return data


def _normalize_tool_collections(data: dict[str, Any]) -> dict[str, Any]:
    """Sort collections within a tool dictionary."""
    data = dict(data)
    schema = data.get("input_schema")
    if isinstance(schema, dict):
        props = schema.get("properties")
        if isinstance(props, list):
            schema["properties"] = sorted(props, key=lambda x: x.get("name", ""))
        req = schema.get("required")
        if isinstance(req, list):
            schema["required"] = sorted(req)
    return data


def _normalize_workflow_collections(data: dict[str, Any]) -> dict[str, Any]:
    """Sort collections within a workflow dictionary."""
    data = dict(data)
    if "nodes" in data and isinstance(data["nodes"], list):
        data["nodes"] = sorted(data["nodes"], key=lambda x: x.get("id", ""))
    if "edges" in data and isinstance(data["edges"], list):
        data["edges"] = sorted(
            data["edges"],
            key=lambda x: (x.get("source_node_id", ""), x.get("target_node_id", "") or ""),
        )
    if "finish_node_ids" in data and isinstance(data["finish_node_ids"], list):
        data["finish_node_ids"] = sorted(data["finish_node_ids"])
    return data


def to_canonical_dict(
    target: AgentIRManifest | AgentSpec | WorkflowSpec | dict[str, Any],
) -> dict[str, Any]:
    """Transform an AgentIR domain entity or dict into a recursively sorted canonical dict."""
    if isinstance(target, AgentIRManifest):
        raw = AgentIRManifestSchema.from_domain(target).model_dump(mode="json")
        normalized = _normalize_manifest_collections(raw)
    elif isinstance(target, AgentSpec):
        raw = AgentSpecSchema.from_domain(target).model_dump(mode="json")
        normalized = _normalize_agent_collections(raw)
    elif isinstance(target, WorkflowSpec):
        raw = WorkflowSpecSchema.from_domain(target).model_dump(mode="json")
        normalized = _normalize_workflow_collections(raw)
    elif isinstance(target, dict):
        normalized = _normalize_manifest_collections(target)
    else:
        raise TypeError(f"Cannot canonicalize unsupported type: {type(target)}")

    canonical_dict = _sort_canonical(normalized)
    assert isinstance(canonical_dict, dict)
    return canonical_dict


def to_canonical_json(
    target: AgentIRManifest | AgentSpec | WorkflowSpec | dict[str, Any],
    indent: int | None = None,
) -> str:
    """Serialize an entity into canonical JSON."""
    canonical_dict = to_canonical_dict(target)
    return json.dumps(
        canonical_dict,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":") if indent is None else (", ", ": "),
    )


def compute_canonical_hash(
    target: AgentIRManifest | AgentSpec | WorkflowSpec | dict[str, Any],
) -> str:
    """Compute the SHA-256 hash over the canonical JSON representation of an entity."""
    canonical_str = to_canonical_json(target)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
