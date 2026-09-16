"""AgentIR analysis layer (Semantic Diff & Verification)."""

from agentir.analysis.diff import (
    DiffCategory,
    DiffEntry,
    SemanticDiffReport,
    compare_agents,
    compare_manifests,
)
from agentir.analysis.verification import (
    VerificationCheck,
    VerificationReport,
    verify_manifest,
)

__all__ = [
    "DiffCategory",
    "DiffEntry",
    "SemanticDiffReport",
    "VerificationCheck",
    "VerificationReport",
    "compare_agents",
    "compare_manifests",
    "verify_manifest",
]
