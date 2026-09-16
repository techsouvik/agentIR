"""Registry for discovering and instantiating framework adapters."""

from agentir.adapters.base import FrameworkAdapter
from agentir.domain.exceptions import AdapterError

_ADAPTER_REGISTRY: dict[str, type[FrameworkAdapter]] = {}


def register_adapter(name: str, adapter_cls: type[FrameworkAdapter]) -> None:
    """Register an adapter class by framework name."""
    _ADAPTER_REGISTRY[name.lower().replace("-", "_")] = adapter_cls


def get_adapter(framework_name: str) -> FrameworkAdapter:
    """Instantiate and return the adapter for the given framework."""
    key = framework_name.lower().replace("-", "_")
    if key not in _ADAPTER_REGISTRY:
        available = list(_ADAPTER_REGISTRY.keys())
        msg = f"No adapter found for framework '{framework_name}'. Available: {available}"
        raise AdapterError(msg, {"requested": framework_name, "available": available})
    adapter_cls = _ADAPTER_REGISTRY[key]
    return adapter_cls()


def list_registered_adapters() -> list[str]:
    """List all registered framework names."""
    return sorted(_ADAPTER_REGISTRY.keys())
