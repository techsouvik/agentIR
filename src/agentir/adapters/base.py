"""Base protocols and contracts for framework adapters."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from agentir.capabilities.status import CapabilitySupport
from agentir.domain.manifest import AgentIRManifest


@runtime_checkable
class FrameworkAdapter(Protocol):
    """Protocol that all framework adapters must satisfy."""

    @property
    def framework_name(self) -> str:
        """Name of the framework (e.g., 'langgraph', 'agno', 'openai_agents', 'lyzr')."""
        ...

    @property
    def framework_version_range(self) -> str:
        """Semver range of supported framework versions."""
        ...

    @property
    def adapter_version(self) -> str:
        """Version of this adapter implementation."""
        ...

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        """Declare capability support for this framework."""
        ...

    def can_import(self, source: Path | str) -> bool:
        """Check whether this adapter can parse the given source artifact."""
        ...

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        """Import framework source artifacts into canonical AgentIRManifest."""
        ...

    def export_manifest(
        self, manifest: AgentIRManifest, target_directory: Path | str
    ) -> list[Path]:
        """Export an AgentIRManifest into target framework source code and configs.

        Returns list of generated file paths.
        """
        ...
