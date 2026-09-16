"""Compatibility analysis engine between AgentIR manifests and target frameworks."""

from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import (
    CapabilitySupport,
    CompatibilityReport,
    SemanticLossRisk,
    SupportLevel,
)
from agentir.domain.exceptions import UnsupportedCapabilityError
from agentir.domain.manifest import AgentIRManifest


def extract_required_capabilities(manifest: AgentIRManifest) -> set[str]:
    """Inspect an AgentIR manifest and determine all required capabilities."""
    required: set[str] = {"model_calling"}

    # Multiple agents implies multi-agent capability
    if len(manifest.agents) > 1 or len(manifest.workflows) > 0:
        required.add("multi_agent")

    # Inspect agents
    for agent in manifest.agents:
        if agent.tools:
            required.add("tool_calling")
            for t in agent.tools:
                if t.requires_approval:
                    required.add("human_approval")
                if t.permissions or t.mcp_server:
                    required.add("sandboxing")

        if agent.output and (agent.output.format == "json" or agent.output.schema_definition):
            required.add("structured_output")

        if agent.memory and agent.memory.memory_type != "none":
            required.add("memory")

        if agent.state:
            required.add("persistent_state")

        if agent.handoffs:
            required.add("handoff")
            required.add("routing")

        if agent.guards:
            required.add("guardrails")

        pol = agent.execution_policy
        if pol.streaming:
            required.add("streaming")
        if pol.retry_limit > 0:
            required.add("retries")
        if pol.timeout_seconds:
            required.add("timeout")
        if pol.requires_human_approval:
            required.add("human_approval")
        if pol.interrupt_before_nodes or pol.interrupt_after_nodes:
            required.add("interrupts")
        if pol.parallel_execution:
            required.add("parallel_execution")

    # Inspect workflows
    for wf in manifest.workflows:
        if wf.state:
            required.add("persistent_state")
            required.add("checkpointing")

        for edge in wf.edges:
            if edge.is_conditional:
                required.add("conditional_edges")
                required.add("routing")

        if wf.execution_policy:
            pol = wf.execution_policy
            if pol.requires_human_approval:
                required.add("human_approval")
            if pol.interrupt_before_nodes or pol.interrupt_after_nodes:
                required.add("interrupts")
            if pol.parallel_execution:
                required.add("parallel_execution")

    if manifest.shared_state:
        required.add("persistent_state")
    if manifest.shared_tools:
        required.add("tool_calling")

    return required


def analyze_compatibility(
    manifest: AgentIRManifest, target_framework: str
) -> CompatibilityReport:
    """Analyze compatibility of an AgentIR manifest against a target framework."""
    target_key = target_framework.lower().replace("-", "_")
    if target_key not in FRAMEWORK_CAPABILITY_MATRICES:
        available = list(FRAMEWORK_CAPABILITY_MATRICES.keys())
        msg = f"Unknown target framework '{target_framework}'. Available: {available}"
        raise UnsupportedCapabilityError(msg, {"target": target_framework, "available": available})

    matrix = FRAMEWORK_CAPABILITY_MATRICES[target_key]
    required_caps = sorted(extract_required_capabilities(manifest))

    native: list[CapabilitySupport] = []
    adapter: list[CapabilitySupport] = []
    emulated: list[CapabilitySupport] = []
    unsupported: list[CapabilitySupport] = []
    risks: list[dict[str, str]] = []
    actions: list[str] = []
    evidence: list[str] = []

    score_total = 0.0

    for cap_id in required_caps:
        support = matrix.get(
            cap_id,
            CapabilitySupport(
                capability_id=cap_id,
                support_level=SupportLevel.UNSUPPORTED,
                semantic_loss_risk=SemanticLossRisk.HIGH,
                description=f"No capability entry in {target_key} matrix.",
            ),
        )

        match support.support_level:
            case SupportLevel.NATIVE:
                native.append(support)
                score_total += 100.0
                evidence.append(f"[NATIVE] {cap_id} is natively supported by {target_key}.")
            case SupportLevel.ADAPTER:
                adapter.append(support)
                score_total += 80.0
                evidence.append(
                    f"[ADAPTER] {cap_id} requires adapter bridging: {support.description}"
                )
                if support.required_adapter_shim:
                    actions.append(f"Install adapter shim: {support.required_adapter_shim}")
            case SupportLevel.EMULATED:
                emulated.append(support)
                score_total += 50.0
                evidence.append(
                    f"[EMULATED] {cap_id} will be emulated: {support.emulation_strategy}"
                )
                risks.append(
                    {
                        "capability": cap_id,
                        "risk_level": support.semantic_loss_risk.value,
                        "strategy": support.emulation_strategy or "Emulation shim",
                    }
                )
                actions.append(
                    f"Review emulation strategy for {cap_id}: {support.emulation_strategy}"
                )
            case SupportLevel.UNSUPPORTED:
                unsupported.append(support)
                score_total += 0.0
                evidence.append(
                    f"[UNSUPPORTED] {cap_id} cannot be represented in {target_key}: "
                    f"{support.description}"
                )
                risks.append(
                    {
                        "capability": cap_id,
                        "risk_level": support.semantic_loss_risk.value,
                        "description": support.description,
                    }
                )
                actions.append(
                    f"ACTION REQUIRED: Remove or manually re-architect {cap_id} for {target_key}."
                )

    score = score_total / len(required_caps) if required_caps else 100.0

    # Incompatible if any required capability is unsupported with HIGH or CRITICAL risk
    has_blocking_unsupported = any(
        u.semantic_loss_risk in (SemanticLossRisk.HIGH, SemanticLossRisk.CRITICAL)
        for u in unsupported
    )
    is_compatible = not has_blocking_unsupported

    return CompatibilityReport(
        target_framework=target_key,
        is_compatible=is_compatible,
        score=score,
        required_capabilities=tuple(required_caps),
        native=tuple(native),
        adapter=tuple(adapter),
        emulated=tuple(emulated),
        unsupported=tuple(unsupported),
        semantic_loss_risks=tuple(risks),
        required_actions=tuple(actions),
        evidence=tuple(evidence),
    )
