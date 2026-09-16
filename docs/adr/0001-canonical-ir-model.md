# ADR 0001: Canonical Intermediate Representation Model

- **Status**: Accepted
- **Date**: 2026-09-16
- **Authors**: AgentIR Architecture Team

## Context

AI agent frameworks represent agents, workflows, tools, and execution parameters using disparate, proprietary abstractions. Migrating between frameworks or maintaining multi-framework deployments creates vendor lock-in and high refactoring costs. We need a unified, framework-independent Intermediate Representation (AgentIR) that captures the full semantic intent of agent systems without imposing runtime overhead or coupling to any specific SDK.

## Decision

We define AgentIR as a pure, declarative domain model consisting of the following primary entities:
1. **Agent**: Identity, role, system instructions, model binding, assigned tools, handoff targets, and execution policies.
2. **ModelSpec**: Provider, model identifier, temperature, max tokens, top-p, and configuration flags.
3. **ToolSpec & ToolInputSchema**: Tool identifier, description, parameters conforming to JSON Schema Draft 7/2020-12, purity flag, approval requirement, and permissions.
4. **WorkflowSpec & NodeSpec & EdgeSpec**: Directed graph topology supporting entry points, finish points, cyclic loops, direct transitions, and conditional edge routers with branch maps.
5. **StateSpec & StateChannelSpec**: State schema with typed fields and reducer operations (e.g. `replace`, `append`, `merge`).
6. **MemorySpec**: Short-term and long-term memory configurations, vector index references, and window sizes.
7. **ExecutionPolicy**: Turn limits, timeouts, retry policies, backoff strategies, and concurrency settings.
8. **HandoffSpec**: Delegated agent target, transfer schema, state filtering, and return policy.
9. **GuardSpec**: Input/output/tool validation rules, safety policies, and fallback actions.
10. **OutputSpec**: Structured output guarantees, Pydantic/JSON Schema target definitions, and markdown formatting flags.
11. **SourceProvenance**: Tracing origin framework, source file/version, and ingestion timestamp without affecting semantic identity.

All domain models are immutable value objects in the domain layer, with Pydantic v2 validation enforced at serialization and ingestion boundaries.

## Alternatives Considered

1. **Adopting an existing framework as the core (e.g. LangChain LCEL or LangGraph)**:
   - *Rejected*: Violates core neutrality. Creates heavy transitive dependencies, breaks when upstream APIs shift, and prevents clean translation to alternate frameworks like Agno or OpenAI Agents.
2. **Untyped JSON/Dictionary representation**:
   - *Rejected*: Fails to provide compile-time guarantees, validation errors, or type safety.
3. **AST-level Python AST representation**:
   - *Rejected*: Ties the representation strictly to Python syntax rather than semantic agent intent; cannot compile to other languages or declarative YAML specs.

## Consequences

- **Positive**: Complete framework independence; zero framework dependencies in core; deterministic serialization; high type safety.
- **Negative**: Requires implementing explicit bidirectional translation adapters for every supported framework.
