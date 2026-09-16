# Changelog

All notable changes to AgentIR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-17

### Added
- **Core Domain & IR**: Framework-neutral immutable value objects (`AgentSpec`, `WorkflowSpec`, `ToolSpec`, `ModelSpec`, `InstructionsSpec`, `StateSpec`, `MemorySpec`, `HandoffSpec`, `GuardSpec`, `OutputSpec`, `SkillSpec`).
- **Pydantic v2 & Canonical Hashing**: Boundary serialization schemas and deterministic SHA-256 canonical hashing across permutations.
- **23-Dimension Capability Taxonomy**: Multi-tier capability matching (`NATIVE`, `ADAPTER`, `EMULATED`, `UNSUPPORTED`) and semantic risk ratings.
- **Framework Adapters**:
  - `LangGraphAdapter`: AST ingestion and `StateGraph` compilation with channel reducers and checkpointers.
  - `AgnoAdapter`: Ingestion and emission of Agno agents, models, instructions, and teams.
  - `OpenAIAgentsAdapter`: Ingestion and emission of OpenAI Agents SDK handoff networks and guardrails.
  - `CrewAIAdapter`: Ingestion and emission of CrewAI Crews, Agents, Tasks, and sequential flows.
  - `LyzrAdapter`: Ingestion and emission of Lyzr Automata tasks and linear pipelines.
  - `MCPAdapter`: Model Context Protocol tool catalog ingestion and executable tool server generation.
- **Compiler Pipeline & Optimization Passes**:
  - Deterministic `PassManager` running in microseconds.
  - `DeadNodeEliminationPass`: Prunes unreachable graph nodes and severed edges.
  - `ToolSchemaNormalizationPass`: Enforces JSON Schema Draft 7/2020-12 constraints.
  - `LoopInvariantPass`: Classifies DAG vs Cyclic workflows and cycle bounds.
  - `MIGRATION_REPORT.md` and `migration_report.json` audit generation.
- **Analysis Engine**:
  - `DeterministicFSM`: $O(1)$ dispatch table compilation and condition collision auditing.
  - `SemanticDiff`: Categorizes changes as `EQUIVALENT`, `METADATA_ONLY`, `ADDITIVE`, `BEHAVIORAL`, or `BREAKING`.
  - `Verification`: Structural validation, reachability analysis, and regex-based secret scanning.
- **Dual Runtime Harness**:
  - `DeterministicRuntime`: $0 offline simulation without external LLMs (`agentir run`).
  - `LiveRuntime`: Live foundation model chat harness (`agentir chat`) supporting Google Gemini, OpenAI, Groq, and local Ollama with tool execution and human approval.
- **Modern Ergonomic CLI**:
  - Zero-config auto-discovery of manifests (`agentir.yaml`).
  - Source framework auto-detection for imports and migrations.
  - Interactive scaffolding wizard (`agentir init`).
  - Interactive conversational REPL.
  - Convenient aliases: `sim`, `opt`, `doc`, `cap`, `show`.
- **Test Suite**: 82 tests across unit, Hypothesis property-based invariants, golden outputs, security boundaries, and CLI.
