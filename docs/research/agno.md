# Research Note: Agno (formerly Phidata)

- **Subject**: Agno Agent & Team Framework
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/agno-agi/agno
  - https://docs.agno.com/

## 1. Observed Concepts & Architecture

Agno is a lightweight, performant, Python-first agent runtime focusing on simplicity and modularity:
- **Agent**: The primary unit containing model, instructions, tools, memory, storage, and knowledge.
  - Initialized with `Agent(name=..., model=..., instructions=..., tools=[...], markdown=True, structured_outputs=True)`.
- **Team / Multi-Agent**: Orchestration of multiple agents with hierarchical leaders or collaborative routing.
- **Workflow**: Step-by-step or deterministic procedures coordinating agent calls with custom Python logic.
- **Storage / Sessions**: Sqlite, Postgres, or Mongo backing for session state and conversational memory.

## 2. Lifecycle & Execution Model

- Agent loop:
  1. Receive user prompt.
  2. Populate context (instructions, session memory, knowledge search).
  3. Invoke LLM with tool schemas.
  4. If tool call requested, invoke tool and append tool response.
  5. Repeat until final completion or max iterations reached.
  6. Save session to storage.
- Synchronous (`agent.run(...)`) and streaming (`agent.run(..., stream=True)`), plus async counterparts (`agent.arun(...)`).

## 3. Tool Abstraction

- Plain Python functions with type hints and docstrings are automatically parsed into tool definitions.
- Pre-built toolkits (`DuckDuckGoTools`, `SqlTools`, etc.) inheriting from `Toolkit`.
- Support for `show_tool_calls`, `tool_call_limit`, and structured tool definitions.

## 4. Memory & State Model

- Session memory (`AgentSession`) records run history and summary.
- Short-term memory: conversation messages.
- Long-term memory: semantic vector search over past conversations.
- Structured session state dictionary attached to sessions.

## 5. Handoffs, Routing & Multi-Agent

- Agents can delegate to sub-agents via team coordination or explicit routing tools.
- Team leaders summarize or synthesize sub-agent outputs.

## 6. Structured Output & Guardrails

- `response_model`: Accepts a Pydantic model and guarantees or validates structured output.
- Simple pre/post processing hooks.

## 7. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **Declarative Agent Specification**: Agno's clean model/instructions/tools/storage breakdown is an ideal reference for AgentIR's `Agent` domain model.
- **Direct Tool Function Signatures**: Capturing Python function schemas directly into JSON Schema representations.
- **Response Model / Structured Output**: Seamless mapping to `OutputSpec`.

### What AgentIR Should Explicitly NOT Adopt:
- Do not import Agno SDK into AgentIR core.
- Avoid coupling AgentIR to Agno-specific storage drivers (e.g. `PgAgentStorage`). Keep storage abstractions generalized in AgentIR.
