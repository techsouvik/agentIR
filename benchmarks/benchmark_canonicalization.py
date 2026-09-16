"""Benchmark measuring canonical hashing, serialization, and compatibility analysis speed."""

import time

from agentir.capabilities.analyzer import analyze_compatibility
from agentir.domain.agent import AgentSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.schema.canonical import compute_canonical_hash
from agentir.schema.serializer import (
    deserialize_manifest_from_yaml,
    serialize_manifest_to_yaml,
)


def run_benchmark(iterations: int = 1000) -> None:
    print(f"=== AgentIR Performance Benchmark ({iterations} iterations) ===")

    tools = [
        ToolSpec(
            id=f"tool_{i}",
            name=f"Tool {i}",
            description="Performs an automated tool action",
            input_schema=ToolInputSchema(
                properties=(
                    ToolParameterProperty(name="param1", type="string", required=True),
                    ToolParameterProperty(name="param2", type="integer", default=10),
                )
            ),
        )
        for i in range(10)
    ]

    agent = AgentSpec(
        id="benchmark_agent",
        name="Benchmark Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o", temperature=0.7),
        instructions=InstructionsSpec(system_prompt="Execute benchmark tasks."),
        tools=tuple(tools),
    )
    manifest = AgentIRManifest(name="Benchmark System", agents=(agent,))

    # 1. Canonical Hashing Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = compute_canonical_hash(manifest)
    dur = time.perf_counter() - start
    rate = iterations / dur
    print(f"1. Canonical Hashing:      {dur:.3f}s total | {rate:.1f} ops/sec")

    # 2. YAML Serialization Benchmark
    start = time.perf_counter()
    yaml_text = ""
    for _ in range(iterations):
        yaml_text = serialize_manifest_to_yaml(manifest)
    dur = time.perf_counter() - start
    rate = iterations / dur
    print(f"2. YAML Serialization:     {dur:.3f}s total | {rate:.1f} ops/sec")

    # 3. YAML Deserialization Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = deserialize_manifest_from_yaml(yaml_text)
    dur = time.perf_counter() - start
    rate = iterations / dur
    print(f"3. YAML Deserialization:   {dur:.3f}s total | {rate:.1f} ops/sec")

    # 4. Compatibility Analysis Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = analyze_compatibility(manifest, "langgraph")
    dur = time.perf_counter() - start
    rate = iterations / dur
    print(f"4. Compatibility Analysis: {dur:.3f}s total | {rate:.1f} ops/sec")
    print("=== Benchmark Completed Successfully ===")


if __name__ == "__main__":
    run_benchmark(1000)
