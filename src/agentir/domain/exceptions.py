"""Typed domain exceptions for AgentIR."""

from typing import Any


class AgentIRError(Exception):
    """Base exception for all AgentIR errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class AgentIRValidationError(AgentIRError):
    """Raised when an AgentIR definition violates structural or semantic invariants."""


class UnsupportedCapabilityError(AgentIRError):
    """Raised when a requested capability is not supported by the target framework."""


class AdapterError(AgentIRError):
    """Raised when an adapter encounters an error during import or export."""


class ImportError(AgentIRError):
    """Raised when importing source artifacts fails."""


class ExportError(AgentIRError):
    """Raised when exporting AgentIR to target framework artifacts fails."""


class CompatibilityError(AgentIRError):
    """Raised when checking compatibility reveals blocking conflicts."""


class SecurityError(AgentIRError):
    """Raised when a security policy or boundary is violated."""


class GraphValidationError(AgentIRValidationError):
    """Raised when graph topology is invalid (e.g., disconnected entry, undefined node)."""
