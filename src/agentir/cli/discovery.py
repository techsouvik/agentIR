"""Manifest discovery and contextual filesystem search utilities."""

from pathlib import Path

DEFAULT_MANIFEST_NAMES = ("agentir.yaml", "agentir.yml", "agentir.json")


def find_manifest(explicit_path: Path | str | None = None) -> Path:
    """Find an AgentIR manifest file from an explicit path or by searching the workspace.

    Args:
        explicit_path: Optional user-supplied path.

    Returns:
        Resolved Path to the manifest file.

    Raises:
        FileNotFoundError: If no valid manifest is found with actionable remediation.
    """
    if explicit_path:
        p = Path(explicit_path).resolve()
        if p.is_file():
            return p
        if explicit_path != Path("agentir.yaml"):
            # User specifically passed a path that does not exist
            raise FileNotFoundError(f"Manifest file not found at '{explicit_path}'.")

    # Search current directory and climb upwards
    cwd = Path.cwd().resolve()
    current: Path | None = cwd

    while current and current != current.parent:
        for candidate_name in DEFAULT_MANIFEST_NAMES:
            candidate = current / candidate_name
            if candidate.is_file():
                return candidate
        # Stop at git root if present
        if (current / ".git").exists():
            break
        current = current.parent

    raise FileNotFoundError(
        "No AgentIR manifest found (searched for agentir.yaml, agentir.yml, agentir.json).\n"
        "Run 'agentir init' to scaffold a new agent system."
    )
