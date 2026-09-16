# Research Note: Strands (Declarative Workflow / Graph Framework)

- **Subject**: Strands Agent / Workflow Architecture
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/
  - Agent workflow literature & declarative execution models

## 1. Observed Concepts & Architecture

Strands represents declarative, dataflow-oriented agent orchestrations:
- **Strand / Fiber**: A lightweight linear or branching sequence of actions executed by an agent.
- **Dataflow Bindings**: Explicit wiring of output variables from step $A$ into input parameters of step $B$.
- **Typed Contracts**: Nodes declare strict input and output type schemas.
- **Failover / Resilience**: Declarative retry, backoff, and fallback strands.

## 2. Execution Model

- Pure dataflow graph where nodes execute when all incoming dependency data contracts are satisfied.
- Dynamic branching evaluated over runtime payload state.

## 3. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- Explicit dataflow mapping between workflow nodes (`Edge.data_mapping` or input/output bindings).
- Retry, timeout, and fallback policies in `ExecutionPolicy`.

### What AgentIR Should Explicitly NOT Adopt:
- Avoid overly complex dataflow macro languages; rely on standard Python expression syntax or path expressions (e.g. `$.state.user_query`).
