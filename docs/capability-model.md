# AgentIR Capability Taxonomy & Compatibility Model

## 1. Capability Taxonomy

AgentIR defines 23 core capabilities across five categories:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Capability Taxonomy                      │
├─────────────────┬───────────────────────────────────────────┤
│ Execution       │ model_calling, tool_calling, streaming,   │
│                 │ structured_output, retries, async_exec    │
├─────────────────┼───────────────────────────────────────────┤
│ Orchestration   │ handoff, routing, conditional_edges,      │
│                 │ parallel_execution, multi_agent           │
├─────────────────┼───────────────────────────────────────────┤
│ State           │ memory, persistent_state, checkpointing   │
├─────────────────┼───────────────────────────────────────────┤
│ Governance      │ human_approval, interrupts, timeout,      │
│                 │ cancellation, guardrails, sandboxing      │
├─────────────────┼───────────────────────────────────────────┤
│ Interoperability│ lifecycle_hooks, middleware, tracing      │
└─────────────────┴───────────────────────────────────────────┘
```

## 2. Multi-Tier Support Levels

Instead of an opaque percentage score, target support for each required capability is classified into one of four deterministic levels:

1. **NATIVE (`native`)**:
   - The target framework natively provides direct, first-class support for the capability without behavioral compromise.
   - Example: `conditional_edges` in LangGraph; `handoff` in OpenAI Agents SDK.

2. **ADAPTER (`adapter`)**:
   - The capability is bridged via a standard AgentIR adapter pattern or wrapper shim without semantic distortion.
   - Example: Mapping `memory` to a LangGraph message channel; bridging `human_approval` via an interactive tool hook in Agno.

3. **EMULATED (`emulated`)**:
   - The capability is simulated using target constructs with acknowledged trade-offs or behavioral differences.
   - Carries an explicit `SemanticLossRisk` rating (`LOW`, `MEDIUM`, `HIGH`).
   - Example: Simulating graph `conditional_edges` via procedural Python `if/else` inside an Agno Workflow.

4. **UNSUPPORTED (`unsupported`)**:
   - The target framework cannot represent or emulate the capability.
   - If the capability carries `HIGH` or `CRITICAL` risk, the migration compiler **halts by default** unless explicitly overridden with `--force`.
   - Example: Graph superstep `checkpointing` in OpenAI Agents SDK or Agno.

## 3. Scoring & Evaluation Algorithm

The compatibility score is calculated as a derived convenience metric:

$$\text{Score} = \frac{\sum_{c \in \text{Required}} \text{Weight}(c)}{|\text{Required}|} \times 100$$

Where:
- $\text{Weight}(\text{NATIVE}) = 1.0$
- $\text{Weight}(\text{ADAPTER}) = 0.8$
- $\text{Weight}(\text{EMULATED}) = 0.5$
- $\text{Weight}(\text{UNSUPPORTED}) = 0.0$

A migration is considered **Incompatible** (`is_compatible = False`) if ANY required capability has an `UNSUPPORTED` status with `HIGH` or `CRITICAL` semantic loss risk.
