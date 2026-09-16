"""Semantic Diff engine for canonical AgentIR entities."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentir.domain.agent import AgentSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.schema.canonical import compute_canonical_hash, to_canonical_dict


class DiffCategory(StrEnum):
    """Categorization of semantic difference severity."""

    EQUIVALENT = "equivalent"
    METADATA_ONLY = "metadata_only"
    ADDITIVE = "additive"
    BEHAVIORAL = "behavioral"
    BREAKING = "breaking"


@dataclass(frozen=True, slots=True)
class DiffEntry:
    """A granular difference between two AgentIR representations."""

    path: str
    category: DiffCategory
    change_type: str  # "added", "removed", "modified"
    explanation: str
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True, slots=True)
class SemanticDiffReport:
    """Structured report classifying semantic and behavioral changes."""

    is_equivalent: bool
    overall_category: DiffCategory
    entries: tuple[DiffEntry, ...] = field(default_factory=tuple)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_equivalent": self.is_equivalent,
            "overall_category": self.overall_category.value,
            "summary": self.summary,
            "differences": [
                {
                    "path": e.path,
                    "category": e.category.value,
                    "change_type": e.change_type,
                    "explanation": e.explanation,
                    "old_value": e.old_value,
                    "new_value": e.new_value,
                }
                for e in self.entries
            ],
        }


def compare_manifests(
    manifest_a: AgentIRManifest,
    manifest_b: AgentIRManifest,
) -> SemanticDiffReport:
    """Compare two manifests semantically, classifying each difference."""
    hash_a = compute_canonical_hash(manifest_a)
    hash_b = compute_canonical_hash(manifest_b)

    if hash_a == hash_b:
        return SemanticDiffReport(
            is_equivalent=True,
            overall_category=DiffCategory.EQUIVALENT,
            entries=(),
            summary="Manifests are canonically equivalent.",
        )

    dict_a = to_canonical_dict(manifest_a)
    dict_b = to_canonical_dict(manifest_b)

    entries: list[DiffEntry] = []
    _diff_dicts(dict_a, dict_b, path="", entries=entries)

    # Determine highest severity category
    category_order = [
        DiffCategory.EQUIVALENT,
        DiffCategory.METADATA_ONLY,
        DiffCategory.ADDITIVE,
        DiffCategory.BEHAVIORAL,
        DiffCategory.BREAKING,
    ]
    highest = DiffCategory.EQUIVALENT
    for e in entries:
        if category_order.index(e.category) > category_order.index(highest):
            highest = e.category

    summary = (
        f"Found {len(entries)} semantic difference(s). "
        f"Highest impact: {highest.value.upper()}."
    )

    return SemanticDiffReport(
        is_equivalent=False,
        overall_category=highest,
        entries=tuple(entries),
        summary=summary,
    )


def compare_agents(agent_a: AgentSpec, agent_b: AgentSpec) -> SemanticDiffReport:
    """Compare two agent definitions semantically."""
    hash_a = compute_canonical_hash(agent_a)
    hash_b = compute_canonical_hash(agent_b)

    if hash_a == hash_b:
        return SemanticDiffReport(
            is_equivalent=True,
            overall_category=DiffCategory.EQUIVALENT,
            entries=(),
            summary="Agents are canonically equivalent.",
        )

    dict_a = to_canonical_dict(agent_a)
    dict_b = to_canonical_dict(agent_b)

    entries: list[DiffEntry] = []
    _diff_dicts(dict_a, dict_b, path="", entries=entries)

    category_order = [
        DiffCategory.EQUIVALENT,
        DiffCategory.METADATA_ONLY,
        DiffCategory.ADDITIVE,
        DiffCategory.BEHAVIORAL,
        DiffCategory.BREAKING,
    ]
    highest = DiffCategory.EQUIVALENT
    for e in entries:
        if category_order.index(e.category) > category_order.index(highest):
            highest = e.category

    return SemanticDiffReport(
        is_equivalent=False,
        overall_category=highest,
        entries=tuple(entries),
        summary=f"Found {len(entries)} difference(s) in agent definition.",
    )


def _classify_change(
    path: str, change_type: str, old_val: Any, new_val: Any
) -> tuple[DiffCategory, str]:
    """Classify a field change into a DiffCategory and generate an explanation."""
    p_lower = path.lower()

    if "provenance" in p_lower or "metadata" in p_lower or "description" in p_lower:
        return (
            DiffCategory.METADATA_ONLY,
            f"Metadata field '{path}' was {change_type}.",
        )

    if "system_prompt" in p_lower or "instructions" in p_lower:
        return (
            DiffCategory.BEHAVIORAL,
            f"System instructions changed at '{path}'; affects agent behavior.",
        )

    if "model" in p_lower or "temperature" in p_lower:
        return (
            DiffCategory.BEHAVIORAL,
            f"Model hyperparameter changed at '{path}': {old_val} -> {new_val}.",
        )

    if "tools" in p_lower:
        if change_type == "removed":
            return (
                DiffCategory.BREAKING,
                f"Tool or parameter removed at '{path}'; downstream callers may fail.",
            )
        if change_type == "added":
            return (
                DiffCategory.ADDITIVE,
                f"New tool or property added at '{path}'.",
            )
        return (
            DiffCategory.BREAKING,
            f"Tool schema modified at '{path}'.",
        )

    if "nodes" in p_lower or "edges" in p_lower:
        if change_type == "removed":
            return (
                DiffCategory.BREAKING,
                f"Workflow node or edge removed at '{path}'.",
            )
        if change_type == "added":
            return (
                DiffCategory.ADDITIVE,
                f"Workflow step added at '{path}'.",
            )
        return (
            DiffCategory.BEHAVIORAL,
            f"Workflow topology altered at '{path}'.",
        )

    if change_type == "removed":
        return DiffCategory.BREAKING, f"Property removed at '{path}'."
    if change_type == "added":
        return DiffCategory.ADDITIVE, f"Property added at '{path}'."
    return DiffCategory.BEHAVIORAL, f"Value changed at '{path}': {old_val} -> {new_val}."


def _diff_dicts(
    d1: dict[str, Any],
    d2: dict[str, Any],
    path: str,
    entries: list[DiffEntry],
) -> None:
    """Recursively diff two dictionaries."""
    keys1 = set(d1.keys())
    keys2 = set(d2.keys())

    # Removed keys
    for k in sorted(keys1 - keys2):
        curr_path = f"{path}.{k}" if path else k
        cat, expl = _classify_change(curr_path, "removed", d1[k], None)
        entries.append(
            DiffEntry(
                path=curr_path,
                category=cat,
                change_type="removed",
                explanation=expl,
                old_value=d1[k],
                new_value=None,
            )
        )

    # Added keys
    for k in sorted(keys2 - keys1):
        curr_path = f"{path}.{k}" if path else k
        cat, expl = _classify_change(curr_path, "added", None, d2[k])
        entries.append(
            DiffEntry(
                path=curr_path,
                category=cat,
                change_type="added",
                explanation=expl,
                old_value=None,
                new_value=d2[k],
            )
        )

    # Common keys
    for k in sorted(keys1 & keys2):
        curr_path = f"{path}.{k}" if path else k
        v1 = d1[k]
        v2 = d2[k]

        if isinstance(v1, dict) and isinstance(v2, dict):
            _diff_dicts(v1, v2, curr_path, entries)
        elif isinstance(v1, list) and isinstance(v2, list):
            _diff_lists(v1, v2, curr_path, entries)
        elif v1 != v2:
            cat, expl = _classify_change(curr_path, "modified", v1, v2)
            entries.append(
                DiffEntry(
                    path=curr_path,
                    category=cat,
                    change_type="modified",
                    explanation=expl,
                    old_value=v1,
                    new_value=v2,
                )
            )


def _diff_lists(
    l1: list[Any],
    l2: list[Any],
    path: str,
    entries: list[DiffEntry],
) -> None:
    """Diff two lists by matching item IDs or indexing."""
    # If list of dicts with 'id' or 'name', match by identifier
    sample = l1[0] if l1 else (l2[0] if l2 else None)
    if isinstance(sample, dict) and ("id" in sample or "name" in sample):
        id_key = "id" if "id" in sample else "name"
        map1: dict[str, dict[str, Any]] = {
            str(item.get(id_key, "")): item for item in l1 if isinstance(item, dict)
        }
        map2: dict[str, dict[str, Any]] = {
            str(item.get(id_key, "")): item for item in l2 if isinstance(item, dict)
        }

        for item_id in sorted(set(map1.keys()) - set(map2.keys())):
            curr_path = f"{path}[{item_id}]"
            cat, expl = _classify_change(curr_path, "removed", map1[item_id], None)
            entries.append(
                DiffEntry(
                    path=curr_path,
                    category=cat,
                    change_type="removed",
                    explanation=expl,
                    old_value=map1[item_id],
                )
            )

        for item_id in sorted(set(map2.keys()) - set(map1.keys())):
            curr_path = f"{path}[{item_id}]"
            cat, expl = _classify_change(curr_path, "added", None, map2[item_id])
            entries.append(
                DiffEntry(
                    path=curr_path,
                    category=cat,
                    change_type="added",
                    explanation=expl,
                    new_value=map2[item_id],
                )
            )

        for item_id in sorted(set(map1.keys()) & set(map2.keys())):
            curr_path = f"{path}[{item_id}]"
            _diff_dicts(map1[item_id], map2[item_id], curr_path, entries)
    else:
        # Simple scalar or unstructured lists
        if l1 != l2:
            cat, expl = _classify_change(path, "modified", l1, l2)
            entries.append(
                DiffEntry(
                    path=path,
                    category=cat,
                    change_type="modified",
                    explanation=expl,
                    old_value=l1,
                    new_value=l2,
                )
            )
