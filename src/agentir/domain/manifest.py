"""AgentIR root manifest domain model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AgentIRValidationError
from agentir.domain.provenance import SourceProvenance
from agentir.domain.skill import SkillSpec
from agentir.domain.state import StateSpec
from agentir.domain.tool import ToolSpec
from agentir.domain.workflow import WorkflowSpec


@dataclass(frozen=True, slots=True)
class AgentIRManifest:
    """The root container for an AgentIR system specification.

    Encompasses agents, multi-agent workflows, shared tools, and shared state models.
    """

    name: str
    ir_version: str = "0.1.0"
    description: str = ""
    agents: Sequence[AgentSpec] = field(default_factory=tuple)
    workflows: Sequence[WorkflowSpec] = field(default_factory=tuple)
    shared_tools: Sequence[ToolSpec] = field(default_factory=tuple)
    shared_skills: Sequence[SkillSpec] = field(default_factory=tuple)
    shared_state: StateSpec | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
    provenance: SourceProvenance | None = None

    def get_agent(self, agent_id: str) -> AgentSpec | None:
        """Find an agent by ID."""
        for a in self.agents:
            if a.id == agent_id:
                return a
        return None

    def get_workflow(self, workflow_id: str) -> WorkflowSpec | None:
        """Find a workflow by ID."""
        for w in self.workflows:
            if w.id == workflow_id:
                return w
        return None

    def validate_invariants(self) -> None:
        """Validate global references and integrity invariants.

        Raises:
            AgentIRValidationError: If duplicate IDs or broken cross-references are detected.
        """
        agent_ids: set[str] = set()
        for a in self.agents:
            if a.id in agent_ids:
                raise AgentIRValidationError(
                    f"Duplicate agent ID detected in manifest: '{a.id}'.",
                    {"agent_id": a.id},
                )
            agent_ids.add(a.id)

        workflow_ids: set[str] = set()
        for w in self.workflows:
            if w.id in workflow_ids:
                raise AgentIRValidationError(
                    f"Duplicate workflow ID detected in manifest: '{w.id}'.",
                    {"workflow_id": w.id},
                )
            workflow_ids.add(w.id)
            w.validate_topology()

        # Validate handoff targets reference valid agents or workflows
        for a in self.agents:
            for handoff in a.handoffs:
                if handoff.target_agent_id not in agent_ids:
                    msg = (
                        f"Agent '{a.id}' declares handoff to unknown agent "
                        f"'{handoff.target_agent_id}'."
                    )
                    raise AgentIRValidationError(
                        msg,
                        {"source_agent": a.id, "target_agent": handoff.target_agent_id},
                    )
