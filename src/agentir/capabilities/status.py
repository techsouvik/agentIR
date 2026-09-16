"""Capability support status and compatibility report models."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SupportLevel(StrEnum):
    """The fidelity level with which a target framework supports a capability."""

    NATIVE = "native"
    ADAPTER = "adapter"
    EMULATED = "emulated"
    UNSUPPORTED = "unsupported"


class SemanticLossRisk(StrEnum):
    """Potential risk of behavioral deviation or semantic loss."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class CapabilitySupport:
    """Detailed support record for a single capability within a target framework."""

    capability_id: str
    support_level: SupportLevel
    semantic_loss_risk: SemanticLossRisk
    description: str = ""
    emulation_strategy: str | None = None
    required_adapter_shim: str | None = None


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    """Comprehensive, explainable compatibility analysis report."""

    target_framework: str
    is_compatible: bool
    score: float  # 0.0 to 100.0 derived convenience metric
    required_capabilities: tuple[str, ...]
    native: tuple[CapabilitySupport, ...] = field(default_factory=tuple)
    adapter: tuple[CapabilitySupport, ...] = field(default_factory=tuple)
    emulated: tuple[CapabilitySupport, ...] = field(default_factory=tuple)
    unsupported: tuple[CapabilitySupport, ...] = field(default_factory=tuple)
    semantic_loss_risks: tuple[dict[str, str], ...] = field(default_factory=tuple)
    required_actions: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary for JSON output."""
        return {
            "target_framework": self.target_framework,
            "is_compatible": self.is_compatible,
            "score": round(self.score, 1),
            "required_capabilities": list(self.required_capabilities),
            "native": [
                {
                    "id": c.capability_id,
                    "level": c.support_level.value,
                    "risk": c.semantic_loss_risk.value,
                    "description": c.description,
                }
                for c in self.native
            ],
            "adapter": [
                {
                    "id": c.capability_id,
                    "level": c.support_level.value,
                    "risk": c.semantic_loss_risk.value,
                    "shim": c.required_adapter_shim,
                    "description": c.description,
                }
                for c in self.adapter
            ],
            "emulated": [
                {
                    "id": c.capability_id,
                    "level": c.support_level.value,
                    "risk": c.semantic_loss_risk.value,
                    "strategy": c.emulation_strategy,
                    "description": c.description,
                }
                for c in self.emulated
            ],
            "unsupported": [
                {
                    "id": c.capability_id,
                    "level": c.support_level.value,
                    "risk": c.semantic_loss_risk.value,
                    "description": c.description,
                }
                for c in self.unsupported
            ],
            "semantic_loss_risks": list(self.semantic_loss_risks),
            "required_actions": list(self.required_actions),
            "evidence": list(self.evidence),
        }
