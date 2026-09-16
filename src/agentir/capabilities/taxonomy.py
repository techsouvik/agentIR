"""AgentIR capability taxonomy and registry."""

from dataclasses import dataclass
from enum import StrEnum


class CapabilityCategory(StrEnum):
    """Categorization of agent capabilities."""

    EXECUTION = "execution"
    ORCHESTRATION = "orchestration"
    STATE = "state"
    GOVERNANCE = "governance"
    INTEROPERABILITY = "interoperability"


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    """Formal definition of an agent capability in the AgentIR taxonomy."""

    id: str
    name: str
    category: CapabilityCategory
    description: str
    maturity: str = "stable"  # "stable", "beta", "experimental"


# Canonical capabilities required by AgentIR Specification
CAPABILITIES: dict[str, CapabilityDefinition] = {
    "model_calling": CapabilityDefinition(
        id="model_calling",
        name="Foundation Model Calling",
        category=CapabilityCategory.EXECUTION,
        description="Invoking LLMs or foundation models with prompts and parameters.",
    ),
    "tool_calling": CapabilityDefinition(
        id="tool_calling",
        name="Tool & Function Calling",
        category=CapabilityCategory.EXECUTION,
        description="Invoking external functions or tools based on structured schemas.",
    ),
    "structured_output": CapabilityDefinition(
        id="structured_output",
        name="Structured Output Schema",
        category=CapabilityCategory.EXECUTION,
        description="Constraining model completion to match a strict JSON or Pydantic schema.",
    ),
    "streaming": CapabilityDefinition(
        id="streaming",
        name="Token & Event Streaming",
        category=CapabilityCategory.EXECUTION,
        description="Real-time streaming of tokens, tool calls, and lifecycle events.",
    ),
    "memory": CapabilityDefinition(
        id="memory",
        name="Conversational Memory",
        category=CapabilityCategory.STATE,
        description="Maintaining short-term context windows or summary histories.",
    ),
    "persistent_state": CapabilityDefinition(
        id="persistent_state",
        name="Persistent State Store",
        category=CapabilityCategory.STATE,
        description="Persisting agent session or workflow state across process restarts.",
    ),
    "checkpointing": CapabilityDefinition(
        id="checkpointing",
        name="Superstep Checkpointing",
        category=CapabilityCategory.STATE,
        description="Snapshotting full state at each execution step for replay/recovery.",
    ),
    "handoff": CapabilityDefinition(
        id="handoff",
        name="Agent-to-Agent Handoff",
        category=CapabilityCategory.ORCHESTRATION,
        description="Explicit delegation of control and context from one agent to another.",
    ),
    "routing": CapabilityDefinition(
        id="routing",
        name="Dynamic Routing",
        category=CapabilityCategory.ORCHESTRATION,
        description="Routing execution to agents or nodes based on runtime classifier or logic.",
    ),
    "conditional_edges": CapabilityDefinition(
        id="conditional_edges",
        name="Conditional Graph Edges",
        category=CapabilityCategory.ORCHESTRATION,
        description="Branching graph traversal based on state predicates or router functions.",
    ),
    "parallel_execution": CapabilityDefinition(
        id="parallel_execution",
        name="Parallel Branch Execution",
        category=CapabilityCategory.ORCHESTRATION,
        description="Executing multiple nodes or tool calls concurrently.",
    ),
    "human_approval": CapabilityDefinition(
        id="human_approval",
        name="Human-in-the-Loop Approval",
        category=CapabilityCategory.GOVERNANCE,
        description="Requiring explicit human confirmation before executing an action or tool.",
    ),
    "interrupts": CapabilityDefinition(
        id="interrupts",
        name="Workflow Interrupts",
        category=CapabilityCategory.GOVERNANCE,
        description="Pausing graph execution before or after specific nodes.",
    ),
    "retries": CapabilityDefinition(
        id="retries",
        name="Automatic Retries & Backoff",
        category=CapabilityCategory.EXECUTION,
        description="Retrying failed model calls or tool executions according to policy.",
    ),
    "timeout": CapabilityDefinition(
        id="timeout",
        name="Execution Timeout Limits",
        category=CapabilityCategory.GOVERNANCE,
        description="Enforcing maximum runtime duration per turn or session.",
    ),
    "cancellation": CapabilityDefinition(
        id="cancellation",
        name="Task Cancellation",
        category=CapabilityCategory.GOVERNANCE,
        description="Gracefully aborting in-flight execution upon user or system signal.",
    ),
    "lifecycle_hooks": CapabilityDefinition(
        id="lifecycle_hooks",
        name="Lifecycle Event Hooks",
        category=CapabilityCategory.GOVERNANCE,
        description="Invoking pre/post step, error, or tool callbacks.",
    ),
    "middleware": CapabilityDefinition(
        id="middleware",
        name="Execution Middleware",
        category=CapabilityCategory.GOVERNANCE,
        description="Pluggable request/response interceptors.",
    ),
    "tracing": CapabilityDefinition(
        id="tracing",
        name="OpenInference / Tracing",
        category=CapabilityCategory.GOVERNANCE,
        description="Emitting telemetry spans for LLM, tool, and agent turns.",
    ),
    "guardrails": CapabilityDefinition(
        id="guardrails",
        name="Input & Output Guardrails",
        category=CapabilityCategory.GOVERNANCE,
        description="Safety filtering, regex checks, or prompt injection defenses.",
    ),
    "sandboxing": CapabilityDefinition(
        id="sandboxing",
        name="Code / Tool Sandboxing",
        category=CapabilityCategory.GOVERNANCE,
        description="Isolating dangerous or state-mutating tool execution in a sandbox.",
    ),
    "multi_agent": CapabilityDefinition(
        id="multi_agent",
        name="Multi-Agent Collaboration",
        category=CapabilityCategory.ORCHESTRATION,
        description="Coordinating teams or networks of heterogeneous agents.",
    ),
    "async_execution": CapabilityDefinition(
        id="async_execution",
        name="Asynchronous Non-blocking Runtime",
        category=CapabilityCategory.EXECUTION,
        description="Native async/await event-loop concurrency.",
    ),
}
