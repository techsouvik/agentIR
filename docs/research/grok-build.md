# Research Note: Grok Build Agent Harness

- **Subject**: Grok Build Terminal AI Coding Agent / Harness
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/xai-org/grok-build

## 1. Observed Concepts & Architecture

Grok Build is an engineering-grade terminal AI coding agent harness developed by xAI. Key architectural pillars:
- **Clean Harness Separation**: Strict decoupling between the execution engine (core harness), user interface (interactive TUI vs headless CLI vs ACP / Agent Communication Protocol mode), and tool runtime.
- **Task Lifecycle**:
  - Structured phases: Task intake -> Workspace discovery -> Planning -> Tool execution loops -> Verification -> Completion summary.
- **Tool System**:
  - Strict parameter validation, execution sandboxing, timeout enforcement, and structured output capture.
  - Granular permission control: read-only tools vs mutating terminal/file operations requiring human approval or headless auto-approvals.
- **Context Management**:
  - Dynamic token budgeting, context pruning, and history truncation policies to prevent context window exhaustion during long-running tasks.
- **Headless & Scriptable Mode**:
  - Emits machine-readable JSON events, exit codes, and structured task logs for automation and CI/CD.

## 2. Relevance to AgentIR

- **Tool Execution & Safety Policies**: Grok Build's distinction between mutating and non-mutating operations matches AgentIR's `Tool.is_pure` / `Tool.requires_approval` domain properties.
- **Lifecycle Hooks**: Pre-step, post-step, and verification hooks can be captured in AgentIR's `ExecutionPolicy`.
- **Headless CLI Principles**: AgentIR CLI must strictly support `--json`, deterministic exit codes, and clean separation between presentation (Rich) and machine-readable data streams.

## 3. Adapter & Design Implications for AgentIR

### What AgentIR Should Adopt:
- **Safety / Permission Attributes on Tools**: `requires_approval`, `is_deterministic`, `timeout_seconds`.
- **Execution Policy Constraints**: `max_turns`, `timeout_seconds`, `retry_policy`.
- **Headless-First CLI**: Support both rich human-facing output and deterministic `--json` streams.

### What AgentIR Should Explicitly NOT Adopt:
- Do not build a TUI editor or full IDE plugin inside AgentIR. AgentIR is a compiler and IR toolchain, not a coding agent harness itself.
