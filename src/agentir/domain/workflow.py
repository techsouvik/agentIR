"""Workflow graph specification domain model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from agentir.domain.edge import EdgeSpec
from agentir.domain.exceptions import GraphValidationError
from agentir.domain.node import NodeSpec
from agentir.domain.policy import ExecutionPolicy
from agentir.domain.provenance import SourceProvenance
from agentir.domain.state import StateSpec


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    """Stateful computational or multi-agent execution graph."""

    id: str
    name: str
    entry_node_id: str
    nodes: Sequence[NodeSpec] = field(default_factory=tuple)
    edges: Sequence[EdgeSpec] = field(default_factory=tuple)
    finish_node_ids: Sequence[str] = field(default_factory=tuple)
    state: StateSpec | None = None
    execution_policy: ExecutionPolicy | None = None
    description: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: SourceProvenance | None = None

    def get_node(self, node_id: str) -> NodeSpec | None:
        """Find a node by identifier."""
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def outgoing_edges(self, node_id: str) -> list[EdgeSpec]:
        """Return all edges originating from the given node."""
        return [e for e in self.edges if e.source_node_id == node_id]

    def validate_topology(self) -> None:
        """Validate topological soundness of the workflow graph.

        Raises:
            GraphValidationError: If references are missing or the graph is structurally invalid.
        """
        node_ids = {n.id for n in self.nodes}

        if self.entry_node_id not in node_ids:
            raise GraphValidationError(
                f"Workflow '{self.id}' entry node '{self.entry_node_id}' is not defined in nodes.",
                {"entry_node_id": self.entry_node_id, "available_nodes": list(node_ids)},
            )

        for fn_id in self.finish_node_ids:
            if fn_id != "END" and fn_id not in node_ids:
                raise GraphValidationError(
                    f"Workflow '{self.id}' finish node '{fn_id}' is not defined in nodes.",
                    {"finish_node_id": fn_id, "available_nodes": list(node_ids)},
                )

        for edge in self.edges:
            if edge.source_node_id not in node_ids:
                raise GraphValidationError(
                    f"Edge originates from undefined node '{edge.source_node_id}'.",
                    {"source_node_id": edge.source_node_id},
                )
            if edge.is_conditional:
                for branch_key, target in edge.path_map.items():
                    if target != "END" and target not in node_ids:
                        msg = (
                            f"Conditional edge from '{edge.source_node_id}' references "
                            f"undefined target '{target}' for branch '{branch_key}'."
                        )
                        raise GraphValidationError(
                            msg,
                            {"branch": branch_key, "target": target},
                        )
            else:
                if edge.target_node_id is None:
                    raise GraphValidationError(
                        f"Non-conditional edge from '{edge.source_node_id}' has no target_node_id.",
                        {"source_node_id": edge.source_node_id},
                    )
                if edge.target_node_id != "END" and edge.target_node_id not in node_ids:
                    raise GraphValidationError(
                        f"Edge targets undefined node '{edge.target_node_id}'.",
                        {"target_node_id": edge.target_node_id},
                    )
