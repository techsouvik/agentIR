# Research Note: LangGraph

- **Subject**: LangGraph (StateGraph, Checkpointing, Multi-Agent Architecture)
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/langchain-ai/langgraph
  - https://langchain-ai.github.io/langgraph/

## 1. Observed Concepts & Architecture

LangGraph models agent execution as a **stateful computational graph**:
- **StateGraph**: The graph container parameterized by a State schema (TypedDict, dataclass, or Pydantic model) with annotated reducer channels (e.g., `Annotated[list, add_messages]`).
- **Nodes**: Regular Python functions or Runnables that accept `(state, config)` and return a partial state update dictionary.
- **Edges**:
  - Direct edges (`add_edge(start_node, end_node)`)
  - Conditional edges (`add_conditional_edges(source, router_function, path_map)`)
  - Entry points (`set_entry_point(...)`) and Finish points (`END`).
- **CompiledGraph**: The compiled executable graph created via `builder.compile(checkpointer=..., interrupt_before=..., interrupt_after=...)`.

## 2. Lifecycle & Execution Model

- **Pregel-inspired Superstep Engine**:
  - In each superstep, active nodes execute concurrently.
  - State updates are collected and applied using declared reducers (e.g. append, overwrite).
  - Next nodes to execute are determined by evaluating outgoing edges and conditional edge routers.
- Cycles are natively supported (looping between agent reasoning, tool execution, human input).

## 3. Tool Abstraction

- `ToolNode`: Pre-built node executing tool calls present in `AIMessage.tool_calls`.
- Tools can be standard Python functions decorated with `@tool` or LangChain `BaseTool` instances.

## 4. Memory & State Model

- **Channel-based State**: State channels define how updates are merged (e.g. `operator.add` for lists, replacement for scalars).
- **Checkpointers**: `BaseCheckpointSaver` (MemorySaver, SqliteSaver, PostgresSaver) persists the full state snapshot at each superstep with thread IDs.

## 5. Handoffs, Routing & Human-in-the-Loop

- **Interrupts**: `interrupt_before` and `interrupt_after` pause execution before/after specified nodes, enabling human-in-the-loop approvals or modifications.
- **Handoffs**: Typically modeled by routing conditional edges to different agent nodes based on state tags or command objects.

## 6. Observability

- Integrates with LangSmith callbacks, recording execution traces for every node invocation and state transition.

## 7. Capability Analysis: LangGraph Strengths & Limitations

- **Strengths**:
  - Extremely expressive for cyclic graphs, complex state transitions, and time-travel debugging.
  - Fine-grained checkpointing and deterministic state replay.
- **Limitations**:
  - Nodes are arbitrary Python functions, making static extraction of node logic from pure AST non-trivial without structured declarations.
  - Highly coupled to LangChain message models in idiomatic usage.

## 8. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **Explicit Graph Topology**: Node definitions, Edge definitions (direct and conditional), and Reducer/State semantics in AgentIR's `Workflow` domain.
- **Channel / Reducer concepts**: In `StateSpec`, allow defining fields with reducer policies (e.g. `append`, `replace`, `merge`).
- **Interrupt / Human Approval flags**: Representing pre/post execution interrupt points.

### What AgentIR Should Explicitly NOT Adopt:
- Do not require Pregel execution runtime in AgentIR.
- Do not make the IR depend on LangGraph classes.
- Target code generation for LangGraph should emit clean `StateGraph` builder patterns without unnecessary boilerplate.
