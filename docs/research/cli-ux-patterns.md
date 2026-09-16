# Research Note: Modern Developer CLI UX Patterns (2026)

- **Subject**: State-of-the-Art Developer CLI Architecture & Ergonomics
- **Date Researched**: September 2026
- **Reference Benchmarks**:
  - Astral `uv` (Fastest Python package manager, zero-config workspace detection)
  - GitHub CLI `gh` (Interactive surveys, headless JSON flags, contextual git awareness)
  - Vercel & Supabase CLIs (Framework auto-detection, interactive scaffolding wizards)
  - xAI Grok Build & Nous Hermes Agent (Interactive agent REPL, headless event streams)

---

## 1. Ergonomic Pillars of Modern CLIs

### 1.1 Zero-Configuration & Context Awareness
Modern developer tools eliminate redundant arguments:
- **Manifest Auto-Discovery**: Tools locate configuration files (`agentir.yaml`, `agentir.yml`, `agentir.json`) by climbing the directory tree rather than requiring explicit file paths.
- **Framework Fingerprinting**: When importing source code, the CLI statically inspects AST imports and structure (e.g. `StateGraph`, `from agno`, `from crewai`) to auto-detect the source framework without requiring mandatory `--from` flags.

### 1.2 Dual-Mode Interaction (Interactive Wizard vs Headless Automation)
- **Interactive TTY Mode**: When executed in an interactive terminal without required flags, commands should guide the user via brief, clear prompts (e.g., scaffolding wizards, multi-turn chat loops).
- **Headless / CI Mode**: When stdout is piped or `--json` / `--quiet` is passed, the CLI runs completely non-interactively, emitting deterministic JSON or stable exit codes.

### 1.3 Conversational Agent REPL (Testing & Simulation)
Traditional CLIs take an input and exit. Agentic CLIs (like Grok Build and Hermes) provide an **interactive simulation REPL**:
- Allows developers to chat with their agent turn-by-turn.
- Renders tool invocations, state snapshots, and guardrail intercepts in real-time.
- Enables rapid iteration without running expensive production LLM calls.

### 1.4 Helpful Error Recovery & Fuzzy Matching
- When a user enters an unrecognized framework name (e.g., `agentir check --target lang-graph` or `openai`), the CLI performs fuzzy string matching and suggests:
  `Did you mean: langgraph?`
- Actionable next steps are always printed at the conclusion of every command.

---

## 2. Adoption Plan for AgentIR CLI

| Current State | Target Enhancement |
| :--- | :--- |
| File path required for `validate`, `inspect`, `check`, `verify`, `run` | Automatic discovery of `agentir.yaml` / `.yml` / `.json` in current directory. |
| `--from` mandatory in `migrate` and `-f` in `import` | Automatic framework fingerprinting from file contents and imports. |
| `agentir init` uses static flags | Interactive wizard prompting for agent name, template, and model when in a TTY. |
| `agentir run` is one-shot only | Interactive conversational REPL where users can chat with the simulated agent. |
| Strict exact framework keys required | Fuzzy matching with smart suggestions (`openai` -> `openai_agents`). |
| Standard command names only | Convenient aliases (`sim` -> `run`, `cap` -> `capabilities`, `doc` -> `doctor`). |
