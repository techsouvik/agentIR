# Contributing to AgentIR

Thank you for your interest in contributing to **AgentIR**! We welcome contributions from developers, researchers, and agent framework creators.

---

## 1. Development Setup

AgentIR uses [uv](https://github.com/astral-sh/uv) for fast, reproducible Python virtual environments.

### Prerequisites
- Python 3.12 or 3.13
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- Git

### Clone & Install
```bash
git clone git@github.com:techsouvik/agentIR.git
cd agentIR

# Create virtual environment with Python 3.12+
uv venv
source .venv/bin/activate

# Install all development and testing dependencies
uv pip install -e ".[dev]"
```

---

## 2. Project Architecture & Layering

AgentIR enforces strict layered boundaries. Before submitting PRs, verify your code respects this hierarchy:

```text
src/agentir/
  domain/         # Pure dataclasses, zero external dependencies
  schema/         # Pydantic v2 boundary models, YAML/JSON serialization, canonical hashing
  capabilities/   # 23-dimension capability taxonomy & compatibility analyzer
  adapters/       # Framework translation boundaries (LangGraph, Agno, OpenAI, CrewAI, Lyzr, MCP)
  compiler/       # Migration compiler & deterministic optimization passes
  analysis/       # Semantic diff, FSM engine, and security verification
  runtime/        # Offline deterministic simulation and live agent chat harness
  cli/            # Typer CLI application and Rich presentation
  infrastructure/ # Structured logging and filesystem utilities
```

### Golden Rules:
1. **Zero Framework Dependencies in Core**: The `domain/`, `schema/`, `compiler/`, and `analysis/` packages must never import framework SDKs (no `langchain`, `agno`, `openai`, `crewai`).
2. **Deterministic Control Plane**: Compilers and analysis passes must never call an LLM. Use symbolic algorithms only.
3. **No Arbitrary Code Execution**: Never call `eval()`, `exec()`, or dynamic `importlib` on untrusted user code.

---

## 3. Running Quality Checks Locally

Before opening a pull request, ensure all checks pass:

```bash
# 1. Run full test suite with coverage
pytest --cov=agentir --cov-report=term-missing

# 2. Run static type checking (strict mode)
mypy src tests

# 3. Run Ruff linter and formatter
ruff check .
ruff format --check .

# 4. Run CLI smoke tests
agentir doctor
agentir capabilities
agentir optimize examples/customer_support_langgraph.yaml
```

---

## 4. Git Commit Guidelines

AgentIR adheres to the **Conventional Commits** specification:

```text
<type>(<scope>): <short description>
```

### Types:
- `feat`: A new user-facing feature or adapter
- `fix`: A bug fix
- `docs`: Documentation updates
- `test`: Adding or updating tests
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance

### Scopes:
`ir`, `schema`, `capabilities`, `adapters`, `compiler`, `analysis`, `runtime`, `cli`, `passes`

### Examples:
- `feat(adapters): add Google ADK translation adapter`
- `fix(schema): handle empty required arrays in tool parameters`
- `test(property): add Hypothesis tests for FSM transition table`
- `docs(cli): document new interactive scaffolding wizard`

---

## 5. Submitting a Pull Request

1. Fork the repository and create a feature branch (`git checkout -b feat/my-new-adapter`).
2. Implement your changes along with corresponding unit and property-based tests.
3. Ensure test coverage remains $\ge 80\%$.
4. Ensure `mypy` and `ruff` pass with zero errors.
5. Push to your fork and submit a Pull Request against the `main` branch.
