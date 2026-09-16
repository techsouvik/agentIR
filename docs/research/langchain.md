# Research Note: LangChain

- **Subject**: LangChain Core & Architecture
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/langchain-ai/langchain
  - https://python.langchain.com/docs/

## 1. Observed Concepts & Architecture

LangChain is built around the **Runnable** protocol (LCEL: LangChain Expression Language).
- **Runnable**: Unified composition interface supporting `invoke`, `batch`, `stream`, `ainvoke`, `abatch`, `astream`, with pipe operators (`|`).
- **PromptTemplate / ChatPromptTemplate**: Parameterized prompt builders.
- **ChatModel**: Abstraction over foundation model APIs, emitting structured `AIMessage`, `HumanMessage`, `SystemMessage`, `ToolMessage`.
- **Tools**: Callables decorated with `@tool` or inheriting from `BaseTool`, with schemas defined via Pydantic `args_schema`.

## 2. Lifecycle & Execution Model

- Functional pipe composition: `prompt | model | parser`.
- Declarative chaining with configuration overrides (`RunnableConfig` carrying callbacks, tags, metadata, run_name).
- Asynchronous and synchronous execution paths.

## 3. Tool Abstraction

- Schema inspection via Pydantic v1/v2 models.
- Tool invocation returns content string or artifact dict, wrapped into `ToolMessage`.
- Tool error handling policies (e.g. `handle_tool_error`).

## 4. Memory & State Model

- Historically `ConversationBufferMemory`, `ChatMessageHistory`.
- Modern LangChain strongly discourages legacy stateful memory classes in favor of external state stores or LangGraph's explicit state channels.

## 5. Handoffs, Routing & Workflows

- Conditional routing via `RunnableBranch` or lambda routing functions.
- Multi-agent coordination was largely migrated to LangGraph.

## 6. Capability Gaps

- Heavy dependency footprint.
- Monolithic class hierarchies (`BaseLanguageModel`, `BaseChatModel`, `RunnableSerializable`).
- Highly dynamic runtime polymorphism makes static semantic extraction difficult.

## 7. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- Standard message representation (`system`, `user`, `assistant`, `tool`).
- Clear tool input schemas derived from JSON Schema / Pydantic models.
- Clean separation of prompt parameters from fixed system instructions.

### What AgentIR Should Explicitly NOT Adopt:
- Do not adopt `Runnable` or pipe operator `|` as an internal IR concept.
- Do not import `langchain-core` or any LangChain packages into the core domain.
- Do not replicate LangChain's deep class inheritance hierarchies.
