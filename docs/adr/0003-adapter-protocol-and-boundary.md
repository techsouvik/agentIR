# ADR 0003: Framework Adapter Protocol and Isolation Boundary

- **Status**: Accepted
- **Date**: 2026-09-16
- **Authors**: AgentIR Architecture Team

## Context

Framework SDKs have large dependency trees, conflicting versions, and dynamic APIs. The core AgentIR package must run without any framework installed (e.g. in CI or resource-constrained CLI environments). Furthermore, importing agent source code must not execute untrusted code or arbitrary side effects.

## Decision

1. **Protocol-Driven Boundaries**:
   Define explicit Python `typing.Protocol` interfaces for adapters:
   - `FrameworkImporter`: parses source files/definitions into AgentIR with provenance.
   - `FrameworkExporter`: compiles AgentIR into target framework code and configurations.
   - `FrameworkCapabilityProvider`: declares supported capability matrices.

2. **Zero Framework Dependencies in Core**:
   The `agentir` core package imports none of `langchain`, `langgraph`, `agno`, `openai`, `crewai`, or `lyzr`. Adapter implementations use standard library AST parsing, structural pattern matching, and template-based or AST-based code emission. Optional dynamic adapters requiring upstream SDKs are isolated under optional feature flags.

3. **Safe Parsing Only**:
   Adapters parsing Python source code use Python's built-in `ast` module to statically extract definitions (Agent instantiations, tool decorators, graph additions). Under no circumstances will AgentIR invoke `eval()`, `exec()`, or `importlib.import_module()` on untrusted user code.

## Alternatives Considered

- **Importing User Modules Directly (`importlib`)**:
  - *Rejected*: Running arbitrary user Python files can execute malicious payloads, trigger network calls, or crash the process.
- **Requiring Framework SDKs as Hard Dependencies**:
  - *Rejected*: Leads to dependency hell (conflicting Pydantic/OpenAI/LangChain versions) and prevents running AgentIR as a lean CLI.

## Consequences

- **Positive**: Exceptional security posture; zero dependency conflicts; fast startup; runs anywhere Python 3.12+ is available.
- **Negative**: AST static extraction must account for varied coding styles; complex dynamic runtime metaprogramming in user code requires clear limitations and fallback documentation.
