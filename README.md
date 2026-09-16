# AgentIR

<p align="center">
  <strong>Framework-neutral Intermediate Representation (IR) and compiler toolchain for autonomous AI agents.</strong>
</p>

<p align="center">
  <a href="https://github.com/techsouvik/agentIR/actions/workflows/ci.yml"><img src="https://github.com/techsouvik/agentIR/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://pypi.org/project/agentir/"><img src="https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg" alt="Python Versions"></a>
  <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/badge/packaged%20with-uv-purple.svg" alt="Packaged with uv"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-green.svg" alt="License"></a>
</p>

---

## What is AgentIR?

**AgentIR** is an intermediate representation and compiler designed to decouple agent architecture from specific runtime frameworks. Much like **LLVM** abstracts hardware instruction sets from programming languages, AgentIR abstracts agent architectures (prompts, tools, models, state graphs, handoffs, and guardrails) from proprietary framework SDKs.

With AgentIR, you write or import an agent definition once, deterministically analyze its compatibility across target frameworks, and compile it into idiomatic, runnable code for:
- **LangGraph**
- **Agno** (formerly Phidata)
- **OpenAI Agents SDK**
- **CrewAI**
- **Lyzr Automata**
- **Model Context Protocol (MCP)**

AgentIR is **not** a runtime wrapper. It generates clean, standalone native source code for target ecosystems without adding runtime dependencies or latency.

---

## Architecture Overview

```text
Source Framework Source / Spec (LangGraph, Agno, OpenAI, CrewAI, MCP)
                         │
                         ▼
             ┌───────────────────────┐
             │   Framework Adapter   │
             └───────────┬───────────┘
                         │ (Statically parsed via Python AST / Safe YAML)
                         ▼
             ┌───────────────────────┐
             │     AgentIR Core      │
             │   (Canonical Model)   │
             └─────┬─────┬─────┬─────┘
                   │     │     │
         ┌─────────┘     │     └─────────┐
         ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌──────────────────┐
│   Capability    │ │ Semantic Diff │ │ Policy & Safety  │
│    Analyzer     │ │    Engine     │ │   Verification   │
└────────┬────────┘ └───────────────┘ └──────────────────┘
         │
         ▼
┌─────────────────┐
│    Compiler     │
└────────┬────────┘
         │
         ▼
Target Framework Code (e.g. LangGraph StateGraph, Agno Agent, CrewAI Crew, MCP Server)
```

---

## Key Features

- **Zero-Dependency Domain Core**: Pure Python immutable value objects. Zero framework SDK dependencies in the core engine.
- **Deterministic Canonical Hashing**: Recursive key sorting, ID-based collection normalization, and ephemeral field scrubbing guarantee that identical agent semantics produce identical SHA-256 digests.
- **23-Dimension Capability Taxonomy**: Categorizes framework support into `NATIVE`, `ADAPTER`, `EMULATED`, and `UNSUPPORTED` with explicit semantic loss risk ratings.
- **Explainable Migration Reports**: Emits rich `MIGRATION_REPORT.md` and `migration_report.json` auditing every preserved, adapted, or emulated capability.
- **Semantic Diff**: Classifies differences between agent versions as `EQUIVALENT`, `METADATA_ONLY`, `ADDITIVE`, `BEHAVIORAL`, or `BREAKING`.
- **Security by Design**: 10MB DoS payload limits, safe YAML parsing, path traversal containment, and regex secret-leak scanning.
- **Deterministic Offline Simulation**: `agentir run` executes step-by-step reasoning, tool dispatch, and guardrail checks locally without API keys.
- **Model Context Protocol (MCP)**: Native tool catalog ingestion and MCP server generation for Claude Desktop and MCP hosts.
- **Modular Skills System**: Reusable skill packages bundling instructions, tool bindings, reference resources, and few-shot examples.

---

## Installation

Install using `uv`:

```bash
uv pip install agentir
```

Or using standard `pip`:

```bash
pip install agentir
```

---

## Quickstart

### 1. Check Installation & Environment
```bash
agentir doctor
```

### 2. Scaffold a New Agent
```bash
agentir init customer_support --template tools -o agentir.yaml
```

### 3. Inspect the Manifest
```bash
agentir inspect agentir.yaml
```

Output:
```text
╭──────────────────────── AgentIR Manifest Inspection ─────────────────────────╮
│ Customer Support (IR 0.1.0)                                                  │
│ ├── Canonical Hash:                                                          │
│ │   321ee18dd2093544c4f69c50f94bcf346df7c91a53227fff3e171dd9148abb5a         │
│ ├── Agents (1)                                                               │
│ │   └── Customer Support Agent (`customer_support_agent`)                    │
│ │       ├── Model: openai/gpt-4o                                             │
│ │       └── Tools (1)                                                        │
│ │           └── Search Tool: Search documentation and web content            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 4. Check Compatibility Against a Target Framework
```bash
agentir check agentir.yaml --target agno
```

### 5. Migrate Code Between Frameworks
```bash
agentir migrate my_langgraph_workflow.py \
  --from langgraph \
  --to agno \
  -o ./migrated_agno_project
```

### 6. Verify Security & Semantic Invariants
```bash
agentir verify agentir.yaml
```

### 7. Run an Offline Dry-Run Simulation
```bash
agentir run agentir.yaml --input "Can you check my tracking status?"
```

---

## Supported Ecosystems

| Ecosystem | Direction | Primary Primitive | Key Strengths |
| :--- | :--- | :--- | :--- |
| **LangGraph** | Bidirectional | `StateGraph` | Cyclic graphs, Pregel superstep checkpointing, time-travel. |
| **Agno** | Bidirectional | `Agent`, `Team` | Fast, lightweight, Pythonic agents with storage backends. |
| **OpenAI Agents**| Bidirectional | `Agent`, `Runner` | Native handoff networks, input/output guardrails, tracing. |
| **CrewAI** | Bidirectional | `Crew`, `Task` | Role-playing teams, backstories, sequential/hierarchical flows. |
| **Lyzr** | Bidirectional | `LinearSyncPipeline` | Task-based pipelines, audit logging, simulation control plane. |
| **MCP** | Bidirectional | JSON-RPC Tool Server | Open standard for tool and context interoperability. |

---

## Command Line Interface (CLI) Reference

| Command | Description |
| :--- | :--- |
| `agentir version` | Show version, IR specification version, and platform info. |
| `agentir doctor` | Run system diagnostics (Python, dependencies, registered adapters). |
| `agentir init` | Scaffold a starter AgentIR YAML/JSON manifest. |
| `agentir validate` | Validate schema syntax and domain graph invariants. |
| `agentir inspect` | Render structured inspection tree with canonical hash. |
| `agentir capabilities`| View capability taxonomy or declared framework support matrix. |
| `agentir check` | Analyze compatibility between manifest and target framework. |
| `agentir import` | Ingest framework source code/fixture into canonical AgentIR. |
| `agentir export` | Compile AgentIR manifest into target framework code & configs. |
| `agentir migrate` | Execute end-to-end multi-framework migration pipeline. |
| `agentir diff` | Compute semantic difference impact (BREAKING vs ADDITIVE). |
| `agentir verify` | Run full verification suite (reachability, cycles, secret leaks). |
| `agentir run` | Offline deterministic turn simulation without external LLMs. |
| `agentir mcp export` | Export tools as an executable MCP tool server. |
| `agentir mcp import` | Ingest tools from an MCP tool catalog JSON into AgentIR. |

Every command supports `--json` for machine-readable CI/CD pipelines.

---

## Documentation

Detailed architectural and developer guides are available in [`docs/`](docs/):

- [System Architecture](docs/architecture.md)
- [IR Specification (v0.1)](docs/ir-spec.md)
- [Capability Taxonomy & Compatibility Model](docs/capability-model.md)
- [Framework Adapter Authoring Guide](docs/adapter-guide.md)
- [Model Context Protocol (MCP) Guide](docs/mcp-guide.md)
- [Modular Skills System Guide](docs/skills-guide.md)
- [Deterministic Runtime Simulation](docs/runtime-simulation.md)
- [Security Model & Threat Mitigation](docs/security.md)
- [Testing Strategy](docs/testing.md)
- [CLI Reference Manual](docs/cli-reference.md)
- [5-Minute Quickstart Tutorial](docs/quickstart.md)
- [Sample Migration Audit Report](docs/migration-report-example.md)
- [Architectural Decision Records (ADRs)](docs/adr/)
- [Upstream Framework Research Notes](docs/research/)

---

## Development & Testing

AgentIR uses `uv` for lightning-fast development environments:

```bash
# Clone the repository
git clone git@github.com:techsouvik/agentIR.git
cd agentIR

# Create virtual environment and install development dependencies
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Run test suite
pytest --cov=agentir --cov-report=term-missing

# Run static type checking
mypy src tests

# Run linter
ruff check .

# Run performance benchmark
python benchmarks/benchmark_canonicalization.py

# Run CLI demo walkthrough
./examples/demo_walkthrough.sh
```

---

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.
