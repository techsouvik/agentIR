"""Registry for discovering and instantiating framework adapters."""

import difflib
from pathlib import Path

from agentir.adapters.base import FrameworkAdapter
from agentir.domain.exceptions import AdapterError

_ADAPTER_REGISTRY: dict[str, type[FrameworkAdapter]] = {}

# Common aliases mapping to primary adapter keys
FRAMEWORK_ALIASES: dict[str, str] = {
    "openai": "openai_agents",
    "open_ai": "openai_agents",
    "swarm": "openai_agents",
    "lang_graph": "langgraph",
    "phidata": "agno",
    "crew": "crewai",
    "lyzr_automata": "lyzr",
}


def register_adapter(name: str, adapter_cls: type[FrameworkAdapter]) -> None:
    """Register an adapter class by framework name."""
    _ADAPTER_REGISTRY[name.lower().replace("-", "_")] = adapter_cls


def get_adapter(framework_name: str) -> FrameworkAdapter:
    """Instantiate and return the adapter for the given framework."""
    resolved, suggestions = resolve_framework_name(framework_name)
    if not resolved:
        available = list_registered_adapters()
        suggestion_msg = f" Did you mean '{suggestions[0]}'?" if suggestions else ""
        msg = (
            f"No adapter found for framework '{framework_name}'.{suggestion_msg} "
            f"Available: {available}"
        )
        raise AdapterError(
            msg,
            {"requested": framework_name, "suggestions": suggestions, "available": available},
        )
    adapter_cls = _ADAPTER_REGISTRY[resolved]
    return adapter_cls()


def list_registered_adapters() -> list[str]:
    """List all registered framework names."""
    return sorted(_ADAPTER_REGISTRY.keys())


def resolve_framework_name(name: str) -> tuple[str | None, list[str]]:
    """Resolve a user-provided framework name, handling aliases and fuzzy suggestions."""
    clean = name.lower().strip().replace("-", "_")

    # Direct match
    if clean in _ADAPTER_REGISTRY:
        return clean, []

    # Alias match
    if clean in FRAMEWORK_ALIASES and FRAMEWORK_ALIASES[clean] in _ADAPTER_REGISTRY:
        return FRAMEWORK_ALIASES[clean], []

    # Fuzzy suggestion
    candidates = list_registered_adapters()
    matches = difflib.get_close_matches(clean, candidates, n=3, cutoff=0.5)
    return None, matches


def detect_framework(source: Path | str) -> str | None:
    """Auto-detect the source framework by probing registered adapters."""
    source_path = Path(source)
    if not source_path.is_file():
        return None

    for name, adapter_cls in _ADAPTER_REGISTRY.items():
        try:
            adapter = adapter_cls()
            if adapter.can_import(source_path):
                return name
        except Exception:
            continue
    return None
