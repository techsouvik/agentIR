# AgentIR Testing Strategy & Quality Assurance

AgentIR adheres to a multi-tiered testing strategy designed to verify determinism, security, round-trip fidelity, and cross-framework code generation.

---

## 1. Test Architecture

The test suite is partitioned into six specialized layers in `tests/`:

```text
tests/
├── unit/         # Unit tests for domain models, schemas, analyzers, and adapters
├── property/     # Property-based invariant testing using Hypothesis
├── golden/       # Golden output validation for emitted framework code
├── security/     # Adversarial testing: safe YAML, DoS limits, and secret leakage
├── cli/          # End-to-end CLI command testing using Typer's CliRunner
└── fixtures/     # Realistic sample files for LangGraph, Agno, OpenAI, CrewAI, Lyzr
```

---

## 2. Testing Layers

### 2.1 Unit Tests (`tests/unit/`)
Tests pure logic and isolated components:
- Domain model invariant validation (e.g. duplicate IDs, malformed graphs).
- Bidirectional Pydantic schema validation.
- Capability extraction from complex agent graphs.
- Compatibility analysis matching algorithm against declared matrices.
- Individual framework adapters (LangGraph, Agno, OpenAI Agents, CrewAI, Lyzr, MCP).

### 2.2 Property-Based Tests (`tests/property/`)
Uses the [Hypothesis](https://hypothesis.readthedocs.io/) library to prove invariants across randomized inputs:
- **Canonical Hash Determinism**: Arbitrary permutations of dictionary keys and collection elements (tools, agents, nodes) produce identical canonical SHA-256 digests.
- **Round-Trip Preservation**: Random valid manifests serialized to YAML and deserialized back yield zero semantic or structural drift.
- **Reflexive Diff Symmetry**: Diffing any manifest against itself (`diff(A, A)`) always yields `EQUIVALENT` with 0 differences.

### 2.3 Golden Tests (`tests/golden/`)
Prevents regression in generated code:
- Compiles fixture manifests against target framework adapters.
- Validates the presence of idiomatic patterns (e.g. `StateGraph(AgentState)` for LangGraph, `Agent(model=OpenAIChat)` for Agno, `Runner.run` for OpenAI Agents, `Crew(agents=...)` for CrewAI).
- Asserts that emitted `requirements.txt` specifies the correct semver ranges.

### 2.4 Security Tests (`tests/security/`)
Adversarial test cases guarding the system against untrusted input:
- **Arbitrary Code Execution Block**: Verifies that custom Python tags (e.g. `!!python/object/apply:os.system`) are rejected by the safe YAML parser.
- **DoS Payload Limits**: Enforces that input documents larger than 10MB raise a `SecurityError` before parsing.
- **Secret Detection**: Asserts that API keys (`sk-...`), Bearer tokens, and credential patterns are caught by `verify_manifest()`.
- **Path Traversal**: Verifies path resolution boundaries preventing output escape.

### 2.5 CLI Integration Tests (`tests/cli/`)
Exercises all commands via Typer's `CliRunner`:
- `version`, `doctor`, `capabilities`, `init`, `validate`, `inspect`, `check`, `import`, `export`, `migrate`, `diff`, `verify`, `run`, `mcp`.
- Validates exit codes (0 for success, 1 for error, 2 for incompatible checks).
- Validates machine-readable output when `--json` flag is provided.

---

## 3. Running the Test Suite

Run all tests with code coverage:
```bash
pytest --cov=agentir --cov-report=term-missing
```

Run only property-based tests:
```bash
pytest tests/property/
```

Run security boundaries:
```bash
pytest tests/security/
```

---

## 4. Quality Standards & Enforcement

In addition to pytest, every change is validated against:
- **Strict Typing**: `mypy src tests` (0 errors in strict mode).
- **Linting & Code Formatting**: `ruff check .`
