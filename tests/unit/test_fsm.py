"""Unit tests for the Deterministic Finite State Machine (FSM) engine."""

from agentir.analysis.fsm import DeterministicFSM
from agentir.domain.edge import EdgeSpec
from agentir.domain.node import NodeSpec
from agentir.domain.workflow import WorkflowSpec


def test_fsm_table_build_and_transitions() -> None:
    nodes = (
        NodeSpec(id="triage", type="agent", name="Triage"),
        NodeSpec(id="billing", type="agent", name="Billing"),
        NodeSpec(id="tech", type="agent", name="Technical"),
    )
    edges = (
        EdgeSpec(
            source_node_id="triage",
            is_conditional=True,
            path_map={"billing_issue": "billing", "tech_issue": "tech", "done": "END"},
        ),
        EdgeSpec(source_node_id="billing", target_node_id="END"),
        EdgeSpec(source_node_id="tech", target_node_id="END"),
    )
    wf = WorkflowSpec(
        id="support_fsm",
        name="Support FSM",
        entry_node_id="triage",
        finish_node_ids=("END",),
        nodes=nodes,
        edges=edges,
    )

    fsm = DeterministicFSM(wf)
    report = fsm.validate_soundness()

    assert report.is_deterministic is True
    assert len(report.collisions) == 0

    # Test O(1) transition dispatch
    next_node = fsm.transition("triage", "billing_issue")
    assert next_node == "billing"

    next_node_tech = fsm.transition("triage", "tech_issue")
    assert next_node_tech == "tech"

    # Terminal state transition returns None
    assert fsm.transition("END") is None


def test_fsm_collision_detection() -> None:
    """Ambiguous identical branch keys to different targets must be flagged as collisions."""
    nodes = (
        NodeSpec(id="router", type="agent", name="Router"),
        NodeSpec(id="target_a", type="agent", name="Target A"),
        NodeSpec(id="target_b", type="agent", name="Target B"),
    )
    # Collision: two edges with identical branch key "conflict" pointing to target_a and target_b
    edges = (
        EdgeSpec(source_node_id="router", is_conditional=True, path_map={"conflict": "target_a"}),
        EdgeSpec(source_node_id="router", is_conditional=True, path_map={"conflict": "target_b"}),
    )
    wf = WorkflowSpec(
        id="colliding_wf",
        name="Colliding FSM",
        entry_node_id="router",
        nodes=nodes,
        edges=edges,
    )

    fsm = DeterministicFSM(wf)
    report = fsm.validate_soundness()

    assert report.is_deterministic is False
    assert len(report.collisions) > 0
    assert any("conflict" in c for c in report.collisions)
