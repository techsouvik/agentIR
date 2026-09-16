# ADR 0002: Capability Taxonomy and Multi-Tier Compatibility Analysis

- **Status**: Accepted
- **Date**: 2026-09-16
- **Authors**: AgentIR Architecture Team

## Context

Target frameworks support different subsets of agent capabilities (e.g., cyclic graphs, streaming, interrupts, tool calling, multi-agent handoffs). A simplistic percentage-based compatibility metric ("85% compatible") hides critical behavioral loss, such as silent failure to enforce interrupts or inability to execute cyclic state loops. We need an explainable, deterministic compatibility analyzer.

## Decision

1. **Taxonomy Definition**: Define a comprehensive taxonomy of 20+ core capabilities:
   - `model_calling`, `tool_calling`, `structured_output`, `streaming`, `memory`, `persistent_state`, `checkpointing`, `handoff`, `routing`, `conditional_edges`, `parallel_execution`, `human_approval`, `interrupts`, `retries`, `timeout`, `cancellation`, `lifecycle_hooks`, `middleware`, `tracing`, `guardrails`, `sandboxing`, `multi_agent`, `async_execution`.

2. **Multi-Tier Status**: For every required capability in an AgentIR graph against a target framework, classify support into one of four statuses:
   - `NATIVE`: The target framework natively and faithfully supports the capability.
   - `ADAPTER`: The capability is bridged via an AgentIR runtime shim/adapter without semantic distortion.
   - `EMULATED`: The capability is simulated using target constructs (e.g. simulating interrupts via sequential manual step-breaks); carries an explicit semantic-loss warning.
   - `UNSUPPORTED`: The target cannot represent or emulate the capability; compilation will halt unless explicitly forced.

3. **Structured Compatibility Report**: The analyzer returns a structured report including exact matches, partial matches, emulations, unsupported items, actionable migration advice, and risk classifications.

## Alternatives Considered

- **Single Floating-Point Score**: Rejected because it creates a false sense of security while ignoring catastrophic semantic loss.
- **LLM-based Compatibility Estimation**: Rejected because it introduces non-determinism, hallucinations, and unreliability into compiler decisions.

## Consequences

- **Positive**: Transparent, explainable compiler diagnostics; prevents silent runtime regressions; guides developers with clear mitigation steps.
- **Negative**: Requires maintaining accurate capability declaration matrices for every supported framework version.
