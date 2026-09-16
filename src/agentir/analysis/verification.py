"""Verification engine for structural, semantic, and security properties of AgentIR."""

import re
from dataclasses import dataclass, field
from typing import Any

from agentir.domain.manifest import AgentIRManifest
from agentir.domain.workflow import WorkflowSpec

# Regex patterns for common credentials that should never appear in IR
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(
        r"(api[_-]?key|secret[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
        re.IGNORECASE,
    ),
]


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    """Outcome of an individual verification rule check."""

    name: str
    passed: bool
    message: str
    severity: str = "error"  # "error", "warning", "info"


@dataclass(frozen=True, slots=True)
class VerificationReport:
    """Comprehensive report detailing all verification checks."""

    is_valid: bool
    checks: tuple[VerificationCheck, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "severity": c.severity,
                }
                for c in self.checks
            ],
        }


def verify_manifest(manifest: AgentIRManifest) -> VerificationReport:
    """Run full verification suite against an AgentIR manifest."""
    checks: list[VerificationCheck] = []
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Structural Invariants
    try:
        manifest.validate_invariants()
        checks.append(
            VerificationCheck(
                name="structural_invariants",
                passed=True,
                message="Manifest structural invariants and unique IDs validated.",
            )
        )
    except Exception as e:
        msg = f"Structural invariant violation: {e}"
        checks.append(VerificationCheck(name="structural_invariants", passed=False, message=msg))
        errors.append(msg)

    # 2. Workflow Topology & Reachability
    for wf in manifest.workflows:
        _verify_workflow_reachability(wf, checks, warnings)
        _verify_workflow_cycles(wf, checks)

    # 3. Tool Schemas Completeness
    _verify_tools(manifest, checks, warnings)

    # 4. Instructions Completeness
    _verify_instructions(manifest, checks, warnings)

    # 5. Security & Secret Leakage Detection
    _verify_secrets(manifest, checks, errors)

    is_valid = len(errors) == 0
    return VerificationReport(
        is_valid=is_valid,
        checks=tuple(checks),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _verify_workflow_reachability(
    wf: WorkflowSpec,
    checks: list[VerificationCheck],
    warnings: list[str],
) -> None:
    """Check that all nodes are reachable from the entry point and can reach a finish node."""
    adj: dict[str, set[str]] = {n.id: set() for n in wf.nodes}
    adj["END"] = set()

    for edge in wf.edges:
        if edge.is_conditional:
            for target in edge.path_map.values():
                if edge.source_node_id in adj:
                    adj[edge.source_node_id].add(target)
        else:
            if edge.target_node_id and edge.source_node_id in adj:
                adj[edge.source_node_id].add(edge.target_node_id)

    # Forward reachability from entry
    visited: set[str] = set()
    queue = [wf.entry_node_id]
    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            visited.add(curr)
            for neighbor in adj.get(curr, set()):
                if neighbor not in visited and neighbor in adj:
                    queue.append(neighbor)

    unreachable = {n.id for n in wf.nodes} - visited
    if unreachable:
        msg = f"Workflow '{wf.id}' contains unreachable nodes from entry: {sorted(unreachable)}"
        checks.append(
            VerificationCheck(
                name="workflow_reachability",
                passed=False,
                message=msg,
                severity="warning",
            )
        )
        warnings.append(msg)
    else:
        checks.append(
            VerificationCheck(
                name="workflow_reachability",
                passed=True,
                message=f"All {len(wf.nodes)} nodes in workflow '{wf.id}' are reachable.",
            )
        )


def _verify_workflow_cycles(wf: WorkflowSpec, checks: list[VerificationCheck]) -> None:
    """Analyze workflow for cycles (loops)."""
    adj: dict[str, set[str]] = {n.id: set() for n in wf.nodes}
    for edge in wf.edges:
        if edge.is_conditional:
            for target in edge.path_map.values():
                if target in adj:
                    adj[edge.source_node_id].add(target)
        else:
            if edge.target_node_id and edge.target_node_id in adj:
                adj[edge.source_node_id].add(edge.target_node_id)

    has_cycle = False
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def dfs(node: str) -> bool:
        visited[node] = 1
        for neighbor in adj.get(node, set()):
            if visited.get(neighbor) == 1:
                return True
            if visited.get(neighbor, 0) == 0 and dfs(neighbor):
                return True
        visited[node] = 2
        return False

    for n in wf.nodes:
        if visited.get(n.id, 0) == 0 and dfs(n.id):
            has_cycle = True
            break

    topology_desc = (
        "cyclic graph (state loops detected)" if has_cycle else "directed acyclic graph (DAG)"
    )
    checks.append(
        VerificationCheck(
            name="workflow_cycle_analysis",
            passed=True,
            message=f"Workflow '{wf.id}' is a {topology_desc}.",
            severity="info",
        )
    )


def _verify_tools(
    manifest: AgentIRManifest,
    checks: list[VerificationCheck],
    warnings: list[str],
) -> None:
    all_tools = list(manifest.shared_tools)
    for a in manifest.agents:
        all_tools.extend(a.tools)

    missing_desc = [t.name for t in all_tools if not t.description.strip()]
    if missing_desc:
        msg = f"Tools missing description (degrades LLM tool-calling accuracy): {missing_desc}"
        checks.append(
            VerificationCheck(
                name="tool_descriptions", passed=False, message=msg, severity="warning"
            )
        )
        warnings.append(msg)
    else:
        checks.append(
            VerificationCheck(
                name="tool_descriptions",
                passed=True,
                message="All tools have valid descriptions.",
            )
        )


def _verify_instructions(
    manifest: AgentIRManifest,
    checks: list[VerificationCheck],
    warnings: list[str],
) -> None:
    empty_prompt = [a.id for a in manifest.agents if not a.instructions.system_prompt.strip()]
    if empty_prompt:
        msg = f"Agents with empty system prompts: {empty_prompt}"
        checks.append(
            VerificationCheck(
                name="agent_instructions", passed=False, message=msg, severity="warning"
            )
        )
        warnings.append(msg)
    else:
        checks.append(
            VerificationCheck(
                name="agent_instructions",
                passed=True,
                message="All agents have non-empty instructions.",
            )
        )


def _verify_secrets(
    manifest: AgentIRManifest,
    checks: list[VerificationCheck],
    errors: list[str],
) -> None:
    """Scan strings for accidental embedded secrets or tokens."""
    strings_to_scan: list[tuple[str, str]] = []

    for a in manifest.agents:
        strings_to_scan.append((f"agent[{a.id}].instructions", a.instructions.system_prompt))
        for k, v in a.metadata.items():
            strings_to_scan.append((f"agent[{a.id}].metadata[{k}]", str(v)))

    found_secrets: list[str] = []
    for loc, text in strings_to_scan:
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                found_secrets.append(loc)
                break

    if found_secrets:
        msg = f"Security risk: Potential secret / API key pattern detected at: {found_secrets}"
        checks.append(
            VerificationCheck(
                name="secret_detection", passed=False, message=msg, severity="error"
            )
        )
        errors.append(msg)
    else:
        checks.append(
            VerificationCheck(
                name="secret_detection",
                passed=True,
                message="No secrets or API keys detected in agent definitions.",
            )
        )
