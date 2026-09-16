# Research Note: CrewAI

- **Subject**: CrewAI Multi-Agent Role-Playing Architecture
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/crewAIInc/crewAI
  - https://docs.crewai.com/

## 1. Observed Concepts & Architecture

CrewAI is built around role-playing multi-agent systems inspired by organizational team structures:
- **Agent**: Defined by `role`, `goal`, `backstory`, `llm`, `tools`, `allow_delegation`, `verbose`, `max_iter`.
- **Task**: Defined by `description`, `expected_output`, `agent`, `tools`, `context` (upstream tasks), `async_execution`, `output_pydantic`.
- **Crew**: The orchestrator encapsulating agents and tasks, configured with a `Process` (`Process.sequential` or `Process.hierarchical` with a manager agent).
- **Flow**: Event-driven workflow system using decorators (`@start`, `@listen`, `@router`) to coordinate stateful, deterministic branching between crews and tasks.

## 2. Lifecycle & Execution Model

- **Sequential**: Tasks run in array order; outputs flow to downstream tasks via `context` declarations.
- **Hierarchical**: A manager agent delegates tasks to specialized worker agents, evaluates results, and requests revisions.
- **Flows**: Event-driven DAGs where methods emit states or signals, triggering `@listen` methods.

## 3. Tool Abstraction

- CrewAI tools inherit from `BaseTool` or wrap callables with `@tool`.
- Tools can be assigned globally to an Agent or scoped to a specific Task.

## 4. Memory & State Model

- Short-term memory (RAG over current crew session).
- Long-term memory (cross-session knowledge via vector store).
- Entity memory (tracking entities discussed during execution).
- Flow state: Pydantic model maintaining global state across flow steps.

## 5. Delegation & Handoffs

- `allow_delegation=True` injects implicit delegation tools (`Delegate work to coworker`, `Ask question to coworker`).
- Manager agent can dynamically re-assign subtasks.

## 6. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **Rich Agent Persona / Instructions**: Role, goal, and backstory map cleanly to AgentIR's `Instructions` (with structured persona components).
- **Task-Scoped Tool Restrictions**: Tools can be declared on the agent or overridden on specific workflow nodes.
- **Delegation Policy**: AgentIR's `ExecutionPolicy` capturing delegation permissions.

### What AgentIR Should Explicitly NOT Adopt:
- Do not make "backstory" a required field for all agents; keep it optional metadata/instruction enrichment.
- Avoid implicit delegation prompts injected invisibly into agent contexts; make delegation explicit in AgentIR `Handoff` or `ExecutionPolicy`.
