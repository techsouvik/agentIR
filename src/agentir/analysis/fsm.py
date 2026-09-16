"""Deterministic Finite State Machine (FSM) engine and transition validator."""

from dataclasses import dataclass, field
from typing import Any

from agentir.domain.workflow import WorkflowSpec


@dataclass(frozen=True, slots=True)
class TransitionEntry:
    """An individual state transition entry in the FSM dispatch table."""

    source_node: str
    event: str
    target_node: str


@dataclass(frozen=True, slots=True)
class FSMValidationReport:
    """Outcome of static FSM transition soundness verification."""

    is_deterministic: bool
    transition_count: int
    collisions: tuple[str, ...] = field(default_factory=tuple)
    dead_end_nodes: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)


class DeterministicFSM:
    """Compiles an AgentIR workflow into an O(1) dispatch transition table."""

    def __init__(self, workflow: WorkflowSpec) -> None:
        self.workflow_id = workflow.id
        self.entry_node = workflow.entry_node_id
        self.finish_nodes = set(workflow.finish_node_ids)
        self.finish_nodes.add("END")

        # Table: source_node -> {event_key: target_node}
        self._table: dict[str, dict[str, str]] = {}
        self.collisions: list[str] = []
        self._build_table(workflow)

    def _build_table(self, workflow: WorkflowSpec) -> None:
        for node in workflow.nodes:
            self._table[node.id] = {}

        for edge in workflow.edges:
            src = edge.source_node_id
            if src not in self._table:
                self._table[src] = {}

            if edge.is_conditional:
                for branch_key, target in edge.path_map.items():
                    if branch_key in self._table[src]:
                        existing = self._table[src][branch_key]
                        if existing != target:
                            self.collisions.append(
                                f"Collision at node '{src}': branch '{branch_key}' ambiguous "
                                f"('{existing}' vs '{target}')."
                            )
                    self._table[src][branch_key] = target
            else:
                target = edge.target_node_id or "END"
                default_key = "__default__"
                if default_key in self._table[src]:
                    existing = self._table[src][default_key]
                    if existing != target:
                        self.collisions.append(
                            f"Collision at node '{src}': multiple unconditional outgoing edges "
                            f"('{existing}' vs '{target}')."
                        )
                self._table[src][default_key] = target

    def transition(self, current_node: str, event_or_branch: str = "") -> str | None:
        """Evaluate next state in O(1) time without calling an LLM."""
        if current_node in self.finish_nodes:
            return None

        node_transitions = self._table.get(current_node)
        if not node_transitions:
            return None

        # 1. Check explicit branch key
        if event_or_branch in node_transitions:
            return node_transitions[event_or_branch]

        # 2. Check default fallback transition
        if "__default__" in node_transitions:
            return node_transitions["__default__"]

        # 3. Fall back to first available branch if any
        if node_transitions:
            return next(iter(node_transitions.values()))

        return None

    def validate_soundness(self) -> FSMValidationReport:
        """Audit the FSM for determinism, transition collisions, and dead-end states."""
        dead_ends: list[str] = []
        notes: list[str] = []

        for node_id, transitions in self._table.items():
            if node_id not in self.finish_nodes and not transitions:
                dead_ends.append(node_id)

        is_deterministic = len(self.collisions) == 0 and len(dead_ends) == 0

        total_transitions = sum(len(t) for t in self._table.values())
        if is_deterministic:
            msg = (
                f"FSM '{self.workflow_id}' is strictly deterministic with "
                f"{total_transitions} transition(s)."
            )
            notes.append(msg)

        return FSMValidationReport(
            is_deterministic=is_deterministic,
            transition_count=total_transitions,
            collisions=tuple(self.collisions),
            dead_end_nodes=tuple(dead_ends),
            notes=tuple(notes),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "entry_node": self.entry_node,
            "finish_nodes": list(self.finish_nodes),
            "table": self._table,
            "collisions": self.collisions,
        }
