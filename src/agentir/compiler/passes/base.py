"""Compiler pass protocol, results, and PassManager pipeline."""

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from agentir.domain.manifest import AgentIRManifest


@dataclass(frozen=True, slots=True)
class PassResult:
    """The diagnostic result of a single compiler pass execution."""

    pass_name: str
    duration_micros: float
    mutations_count: int = 0
    messages: Sequence[str] = field(default_factory=tuple)


class CompilerPass(Protocol):
    """Protocol for a deterministic symbolic compiler pass over an AgentIR manifest."""

    @property
    def name(self) -> str:
        """Name of the optimization or analysis pass."""
        ...

    def run(self, manifest: AgentIRManifest) -> tuple[AgentIRManifest, PassResult]:
        """Execute the pass and return the (potentially transformed) manifest and result."""
        ...


class PassManager:
    """Coordinates and executes a deterministic pipeline of compiler passes in microsecond time."""

    def __init__(self, passes: Sequence[CompilerPass] | None = None) -> None:
        self._passes: list[CompilerPass] = list(passes or [])

    def add_pass(self, compiler_pass: CompilerPass) -> None:
        """Register a compiler pass to the pipeline."""
        self._passes.append(compiler_pass)

    def run(self, manifest: AgentIRManifest) -> tuple[AgentIRManifest, list[PassResult]]:
        """Run all registered passes sequentially over the manifest."""
        current_manifest = manifest
        results: list[PassResult] = []

        for p in self._passes:
            start = time.perf_counter()
            current_manifest, res = p.run(current_manifest)
            elapsed_micros = (time.perf_counter() - start) * 1_000_000

            # Record final timing
            results.append(
                PassResult(
                    pass_name=res.pass_name,
                    duration_micros=round(elapsed_micros, 2),
                    mutations_count=res.mutations_count,
                    messages=res.messages,
                )
            )

        return current_manifest, results
