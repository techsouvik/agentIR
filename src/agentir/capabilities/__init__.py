"""AgentIR capability taxonomy and compatibility analysis."""

from agentir.capabilities.analyzer import (
    analyze_compatibility,
    extract_required_capabilities,
)
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import (
    CapabilitySupport,
    CompatibilityReport,
    SemanticLossRisk,
    SupportLevel,
)
from agentir.capabilities.taxonomy import (
    CAPABILITIES,
    CapabilityCategory,
    CapabilityDefinition,
)

__all__ = [
    "CAPABILITIES",
    "FRAMEWORK_CAPABILITY_MATRICES",
    "CapabilityCategory",
    "CapabilityDefinition",
    "CapabilitySupport",
    "CompatibilityReport",
    "SemanticLossRisk",
    "SupportLevel",
    "analyze_compatibility",
    "extract_required_capabilities",
]
