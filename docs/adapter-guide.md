# Authoring AgentIR Framework Adapters

## 1. Adapter Contract

All framework adapters implement the `FrameworkAdapter` protocol defined in `agentir.adapters.base`:

```python
from pathlib import Path
from agentir.capabilities.status import CapabilitySupport
from agentir.domain.manifest import AgentIRManifest

class FrameworkAdapter(Protocol):
    framework_name: str
    framework_version_range: str
    adapter_version: str

    def get_capabilities(self) -> dict[str, CapabilitySupport]: ...
    def can_import(self, source: Path | str) -> bool: ...
    def import_manifest(self, source: Path | str) -> AgentIRManifest: ...
    def export_manifest(self, manifest: AgentIRManifest, target_directory: Path | str) -> list[Path]: ...
```

## 2. Ingestion Rules (Safety First)

1. **Never Execute User Code**:
   - Do NOT use `exec()`, `eval()`, or `importlib.import_module()`.
   - Use Python's built-in `ast` module to statically inspect source code:
     - Search for `ast.Call` nodes instantiating `Agent(...)` or `StateGraph(...)`.
     - Extract parameters from `ast.Constant` values and keywords.
2. **Preserve Source Provenance**:
   - Attach a `SourceProvenance` instance to all imported agents and workflows.
   - Record `source_framework`, `source_identifier`, `source_file`, and version.

## 3. Code Generation Rules

1. **Header Identification**:
   - Every generated file must include a header indicating it was compiled by AgentIR.
2. **Requirements File**:
   - Always emit a `requirements.txt` with pinned or minimum version constraints for the target framework SDK.
3. **No Unnecessary Framework Abstractions**:
   - Emit idiomatic code following the target framework's standard documentation style rather than wrapping it in an obscure meta-layer.

## 4. Registering New Adapters

Register new adapters in `agentir.adapters.registry`:

```python
from agentir.adapters.registry import register_adapter
from my_custom_adapter import CustomAdapter

register_adapter("my_framework", CustomAdapter)
```
