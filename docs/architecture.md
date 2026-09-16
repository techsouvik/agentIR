# AgentIR System Architecture

## 1. Executive Overview

AgentIR is a framework-neutral intermediate representation (IR) and compiler toolchain for autonomous AI agents. Drawing inspiration from compiler architectures like LLVM, AgentIR decouples the semantic intent of agentic software (personas, prompt templates, tool definitions, execution constraints, graph topologies, memory, and state transitions) from framework-specific runtime SDKs (LangGraph, Agno, OpenAI Agents SDK, CrewAI, Lyzr).

## 2. Layered Architecture

AgentIR enforces a strict unidirectional dependency hierarchy:

```text
┌──────────────────────────────────────────────────────────┐
│                   CLI Presentation                       │
│             (agentir / Typer + Rich)                     │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│              Application & Compiler Pipeline             │
│   (plan_migration, compile_migration, verify_manifest)   │
└─────────────┬──────────────────────────────┬─────────────┘
              │                              │
              ▼                              ▼
┌───────────────────────────┐  ┌───────────────────────────┐
│     Framework Adapters    │  │   Analysis & Capabilities │
│ (LangGraph, Agno, OpenAI) │  │(Compatibility, Diff, Ver.)│
└─────────────┬─────────────┘  └─────────────┬─────────────┘
              │                              │
              ▼                              ▼
┌──────────────────────────────────────────────────────────┐
│               Schema & Serialization Layer               │
│         (Pydantic v2, YAML/JSON, Canonical Hash)         │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   Pure Domain Models                     │
│     (AgentSpec, WorkflowSpec, ToolSpec, StateSpec)       │
│                [Zero External Dependencies]              │
└──────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

1. **Domain Layer (`agentir.domain`)**:
   - Contains pure, immutable Python value objects (using `@dataclass(frozen=True, slots=True)`).
   - Zero third-party dependencies.
   - Houses typed domain exceptions (`AgentIRValidationError`, `GraphValidationError`, `CompatibilityError`, `SecurityError`).

2. **Schema Layer (`agentir.schema`)**:
   - Pydantic v2 models that validate inputs at serialization boundaries.
   - Deterministic canonicalization: sorts dictionaries recursively by key, sorts collections (tools, handoffs, agents, nodes) by unique identifier.
   - Canonical hashing: Computes SHA-256 digests over normalized, canonical JSON representation (excluding ephemeral timestamps).

3. **Capability Layer (`agentir.capabilities`)**:
   - Taxonomy of 23+ canonical agent capabilities categorized into execution, orchestration, state, and governance.
   - Declarative capability support matrices for target frameworks.
   - Compatibility analyzer assessing native support, adapter requirements, emulation strategies, and semantic loss risks.

4. **Adapter Layer (`agentir.adapters`)**:
   - Framework-specific translation boundaries implementing the `FrameworkAdapter` protocol.
   - Safe parsing only: AST static parsing and declarative YAML/JSON fixtures. No arbitrary code execution or `eval()`.
   - Code emitters generating idiomatic, clean Python target source code without runtime framework wrapping.

5. **Compiler Layer (`agentir.compiler`)**:
   - Orchestrates migration planning, safety validation, compatibility verification, code generation, and audit reporting.

6. **Analysis Layer (`agentir.analysis`)**:
   - Semantic Diff: Compares canonical AgentIR representations, categorizing changes as `EQUIVALENT`, `METADATA_ONLY`, `ADDITIVE`, `BEHAVIORAL`, or `BREAKING`.
   - Verification Engine: Enforces structural soundness, graph reachability, loop detection, tool parameter schemas, and secret leakage prevention.

7. **CLI Layer (`agentir.cli`)**:
   - 12 production-grade CLI commands with Rich terminal formatting and full `--json` support for headless automation.
