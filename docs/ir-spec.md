# AgentIR Intermediate Representation Specification (v0.1)

## 1. Specification Status & Invariants

AgentIR v0.1 defines the canonical domain entities required to represent agents and workflows across modern agent ecosystems.

### Core Invariants:
1. **Determinism**: Any two AgentIR objects with identical semantics produce identical canonical SHA-256 digests.
2. **Framework Neutrality**: Domain definitions contain no imports or types from framework SDKs.
3. **Immutability**: Domain models are immutable value objects.
4. **Safety**: Definitions are purely declarative and can be statically parsed without code execution.

---

## 2. Primary Entities

### 2.1 AgentSpec
The primary autonomous or role-playing agent definition.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique stable identifier (e.g. `triage_agent`). |
| `name` | `str` | Display name for the agent. |
| `model` | `ModelSpec` | Model binding and generation hyperparameters. |
| `instructions`| `InstructionsSpec` | System prompt, persona, role, and guidelines. |
| `tools` | `tuple[ToolSpec, ...]` | Tools accessible to the agent. |
| `handoffs` | `tuple[HandoffSpec, ...]`| Explicit delegation targets. |
| `memory` | `MemorySpec \| None` | Conversational buffer or vector store policy. |
| `state` | `StateSpec \| None` | Typed state schema and channel reducers. |
| `execution_policy`| `ExecutionPolicy` | Turn limits, timeouts, retries, and approval flags. |
| `output` | `OutputSpec \| None` | Structured output guarantees. |
| `guards` | `tuple[GuardSpec, ...]` | Input/output validation rules. |
| `metadata` | `Mapping[str, str]` | User-defined key-value attributes. |
| `provenance` | `SourceProvenance \| None`| Ingestion origin, source framework, and file. |

---

### 2.2 WorkflowSpec
Stateful computational or multi-agent execution graph.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique workflow identifier. |
| `name` | `str` | Workflow name. |
| `entry_node_id`| `str` | Starting node in the graph. |
| `finish_node_ids`| `tuple[str, ...]`| Terminal node IDs or `END`. |
| `nodes` | `tuple[NodeSpec, ...]` | List of computational or router nodes. |
| `edges` | `tuple[EdgeSpec, ...]` | Direct or conditional transition edges. |
| `state` | `StateSpec \| None` | Shared graph state model. |
| `execution_policy`| `ExecutionPolicy \| None`| Step timeouts and interrupt nodes. |

---

### 2.3 ToolSpec & ToolInputSchema
Declarative tool definition adhering to JSON Schema Draft 7 / 2020-12.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Tool identifier. |
| `name` | `str` | Callable name. |
| `description`| `str` | Docstring describing tool behavior and use-cases. |
| `input_schema`| `ToolInputSchema` | Properties, parameter types, defaults, required keys. |
| `is_pure` | `bool` | True if calling has no external side effects. |
| `requires_approval`| `bool` | True if human confirmation is required before execution. |
| `timeout_seconds`| `float \| None`| Max execution time. |
| `permissions`| `tuple[str, ...]`| Required security envelopes (e.g. `fs:read`). |

---

### 2.4 StateSpec & StateChannelSpec
Channel-based state schema with update reducers.

- `schema_name`: Name of the state class / TypedDict.
- `channels`: List of `StateChannelSpec(key, type_name, reducer, default_value)`.
- Supported Reducers:
  - `replace`: Overwrite previous value.
  - `append`: Concatenate to list/sequence.
  - `merge`: Deep merge dictionaries.
  - `custom`: Framework-specific custom reducer callable.
