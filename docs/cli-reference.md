# AgentIR CLI Reference Manual

The `agentir` CLI is the developer interface for inspecting, validating, analyzing, compiling, simulating, and running AgentIR systems.

---

## Ergonomic Features & Modern CLI UX

- **Zero-Config Auto-Discovery**: When `PATH` is omitted from `validate`, `inspect`, `check`, `export`, `verify`, or `run`, AgentIR automatically discovers `agentir.yaml`, `agentir.yml`, or `agentir.json` in the current directory or parent directories.
- **Framework Auto-Detection**: When importing or migrating code, `--framework` and `--from` can be omitted; AgentIR statically inspects imports and AST structure to fingerprint the source framework automatically.
- **Interactive Scaffolding Wizard**: Running `agentir init` in an interactive terminal prompts with friendly defaults.
- **Interactive Simulation REPL**: Running `agentir run` without an input prompt launches an interactive conversational chat session with the simulated agent.
- **Fuzzy Target Matching**: Catches typos like `--target open_agents` and suggests `Did you mean 'openai_agents'?`.
- **Command Aliases**:
  - `agentir sim`: Alias for `agentir run`
  - `agentir doc`: Alias for `agentir doctor`
  - `agentir cap`: Alias for `agentir capabilities`
  - `agentir show`: Alias for `agentir inspect`

---

## Global Options

- `-v`, `--verbose`: Enable detailed debug logging.
- `-q`, `--quiet`: Suppress non-essential terminal output.
- `--help`: Display command options and exit.

---

## Commands

### `agentir version`
Print version, IR specification version, runtime platform, and registered adapters.

**Flags:**
- `--json`: Output structured JSON.

**Example:**
```bash
agentir version
agentir version --json
```

---

### `agentir doctor`
Perform system health diagnostics (Python version, dependency verification, registered adapters, write permissions).

**Flags:**
- `--json`: Output structured JSON.

**Example:**
```bash
agentir doctor
```

---

### `agentir init`
Scaffold a starter AgentIR manifest file with best practices.

**Arguments:**
- `NAME`: Name of the agent system (default: `my_agent`).

**Options:**
- `-o`, `--output PATH`: Target file path (default: `agentir.yaml`).
- `-t`, `--template TEMPLATE`: Template preset: `minimal` | `tools` | `multi-agent`.

**Example:**
```bash
agentir init customer_support --template tools -o support.yaml
```

---

### `agentir validate`
Validate syntax, schema, and domain invariants of an AgentIR manifest.

**Arguments:**
- `PATH`: Path to the manifest file (default: `agentir.yaml`).

**Options:**
- `--json`: Output machine-readable JSON.

**Exit Codes:**
- `0`: Valid manifest.
- `1`: Validation error or schema violation.

**Example:**
```bash
agentir validate support.yaml
```

---

### `agentir inspect`
Display an interactive Rich terminal tree of agents, tools, workflows, state channels, and canonical hash.

**Arguments:**
- `PATH`: Path to the manifest file.

**Options:**
- `--json`: Output full structural JSON representation.

**Example:**
```bash
agentir inspect support.yaml
```

---

### `agentir capabilities`
View the 23-dimension canonical capability taxonomy or declared support matrices for target frameworks.

**Options:**
- `-f`, `--framework NAME`: Framework name (`langgraph`, `agno`, `openai_agents`, `crewai`, `lyzr`, `mcp`).
- `--json`: Output JSON representation.

**Example:**
```bash
agentir capabilities --framework langgraph
agentir capabilities --json
```

---

### `agentir check`
Analyze compatibility between an AgentIR manifest and a target framework before compiling.

**Arguments:**
- `PATH`: Path to the manifest file.

**Options:**
- `-t`, `--target FRAMEWORK`: Target framework name (**required**).
- `--json`: Output structured compatibility report JSON.

**Exit Codes:**
- `0`: Compatible.
- `1`: General error.
- `2`: Incompatible (target framework cannot support required capabilities).

**Example:**
```bash
agentir check support.yaml --target openai_agents
```

---

### `agentir import`
Ingest source code, declarative configurations, or fixtures into canonical AgentIR.

**Arguments:**
- `SOURCE`: Path to source file or fixture.

**Options:**
- `-f`, `--framework FRAMEWORK`: Source framework name (**required**).
- `-o`, `--output PATH`: Output path for generated AgentIR YAML/JSON.
- `--format yaml|json`: Serialization format (default: `yaml`).
- `--json`: Machine-readable confirmation.

**Example:**
```bash
agentir import sample_graph.py --framework langgraph -o imported_graph.yaml
```

---

### `agentir export`
Compile an AgentIR manifest into target framework source code and dependency manifests.

**Arguments:**
- `PATH`: Path to AgentIR manifest.

**Options:**
- `-t`, `--target FRAMEWORK`: Target framework name (**required**).
- `-o`, `--output DIR`: Target output directory (default: `dist`).
- `--json`: Output JSON manifest of generated files.

**Example:**
```bash
agentir export support.yaml --target agno -o ./dist_agno
```

---

### `agentir migrate`
Execute an end-to-end multi-framework migration (Source -> AgentIR -> Target + Audit Report).

**Arguments:**
- `SOURCE`: Source artifact file to migrate.

**Options:**
- `--from FRAMEWORK`: Source framework name (**required**).
- `--to FRAMEWORK`: Target framework name (**required**).
- `-o`, `--output DIR`: Destination output directory (default: `migrated_project`).
- `--force`: Force compilation despite capability incompatibilities.
- `--json`: Machine-readable output.

**Example:**
```bash
agentir migrate langgraph_app.py --from langgraph --to agno -o ./migrated_agno --force
```

---

### `agentir diff`
Compare two AgentIR definitions semantically, classifying each change as `EQUIVALENT`, `METADATA_ONLY`, `ADDITIVE`, `BEHAVIORAL`, or `BREAKING`.

**Arguments:**
- `PATH_A`: First manifest file.
- `PATH_B`: Second manifest file.

**Options:**
- `--json`: Output structured diff entries JSON.

**Exit Codes:**
- `0`: Manifests are canonically equivalent.
- `1`: Manifests have differences.

**Example:**
```bash
agentir diff v1.yaml v2.yaml
```

---

### `agentir verify`
Run security, topology, and integrity verification suite. Checks for leaked secrets, unreachable nodes, graph loops, and parameter schema completeness.

**Arguments:**
- `PATH`: Path to AgentIR manifest.

**Options:**
- `--json`: Output validation report JSON.

**Example:**
```bash
agentir verify support.yaml
```

---

### `agentir run`
Simulate agent turns, tool calls, and state transitions offline without external LLM API keys (or connect to real models with `--live`).

**Arguments:**
- `PATH`: Path to AgentIR manifest (auto-discovered if omitted).

**Options:**
- `-i`, `--input TEXT`: User prompt message (default: `"Hello"`).
- `--max-turns N`: Maximum simulated turns (default: 10).
- `--live`: Connect to live foundation model (delegates to `agentir chat`).
- `--json`: Output step-by-step trace JSON.

**Example:**
```bash
agentir run support.yaml --input "Check order #1042"
agentir run --live
```

---

### `agentir chat`
Chat live with an AgentIR agent using real foundation models (OpenAI, local Ollama, OpenRouter, Groq).

**Arguments:**
- `PATH`: Path to AgentIR manifest (auto-discovered if omitted).

**Options:**
- `--base-url URL`: Endpoint base URL (e.g. `http://localhost:11434/v1` for local Ollama).
- `--api-key KEY`: API key (or reads `OPENAI_API_KEY` from environment).
- `-m`, `--model ID`: Override model identifier.

**Example:**
```bash
# Chat using OpenAI
export OPENAI_API_KEY=sk-...
agentir chat

# Chat using local Ollama (100% private, free)
agentir chat --base-url http://localhost:11434/v1 -m llama3
```

---

### `agentir mcp export`
Export tools from an AgentIR manifest as an executable Model Context Protocol (MCP) server.

**Options:**
- `-o`, `--output DIR`: Directory for `mcp_server.py` and `claude_desktop_config.json`.

**Example:**
```bash
agentir mcp export support.yaml -o ./my_mcp_server
```

---

### `agentir mcp import`
Import tools from an MCP tool catalog JSON into an AgentIR manifest.

**Arguments:**
- `SOURCE`: Path to MCP tools JSON catalog.

**Options:**
- `-o`, `--output PATH`: Target AgentIR YAML file.

**Example:**
```bash
agentir mcp import catalog.json -o tools_manifest.yaml
```
