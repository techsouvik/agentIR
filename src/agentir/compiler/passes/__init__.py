"""Deterministic compiler passes and pass pipeline."""

from agentir.compiler.passes.base import CompilerPass, PassManager, PassResult
from agentir.compiler.passes.dead_code import DeadNodeEliminationPass
from agentir.compiler.passes.loop_analysis import LoopInvariantPass
from agentir.compiler.passes.tool_norm import ToolSchemaNormalizationPass


def create_default_pass_pipeline() -> PassManager:
    """Instantiate a PassManager pre-loaded with standard deterministic optimization passes."""
    pipeline = PassManager()
    pipeline.add_pass(DeadNodeEliminationPass())
    pipeline.add_pass(ToolSchemaNormalizationPass())
    pipeline.add_pass(LoopInvariantPass())
    return pipeline


__all__ = [
    "CompilerPass",
    "DeadNodeEliminationPass",
    "LoopInvariantPass",
    "PassManager",
    "PassResult",
    "ToolSchemaNormalizationPass",
    "create_default_pass_pipeline",
]
