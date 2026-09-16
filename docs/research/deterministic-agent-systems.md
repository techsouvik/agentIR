# Research Note: Deterministic Agent Systems & Compiler Pipelines (Zero-LLM Control Plane)

- **Subject**: Architectures for Deterministic Control, Optimization Passes, and Fast Compilers
- **Date Researched**: September 2026
- **Benchmark Systems Studied**:
  - **LLVM Optimizer Pipeline (`opt`)**: Symbolic intermediate representation, analysis and transformation passes, fixed-point iteration.
  - **Temporal.io**: Deterministic workflow replay, event sourcing, non-deterministic boundary isolation.
  - **Google Pregel / BSP**: Bulk Synchronous Parallel supersteps, associative and commutative state reducers.
  - **Outlines / SGLang**: Finite State Automata (FSA) and Context-Free Grammar (CFG) constraint engines.
  - **W3C SCXML / XState**: Hierarchical statecharts, guarded transitions, deterministic collision resolution.

---

## 1. Why Eliminate LLMs from the Control Plane?

Many brittle agent systems make the mistake of using an LLM to decide *how to compile, route, or optimize* an agent at runtime:
1. **Unacceptable Latency**: Calling an LLM takes 500ms–3,000ms. A deterministic compiler pass executes in **0.01ms–0.1ms** (10,000x faster).
2. **Nondeterministic Hallucinations**: An LLM compiler pass can invent invalid tool parameters, drop edges, or alter schemas intermittently.
3. **Flaky CI/CD**: You cannot run deterministic unit tests or regression checks in CI if the compiler itself depends on stochastic model outputs.
4. **Cost**: Running LLMs on every static analysis check or migration incurs unnecessary token costs.

**Fundamental Law**: *Use foundation models exclusively for probabilistic reasoning and text generation; use deterministic symbolic compiler algorithms for all schema validation, graph analysis, optimization passes, and code generation.*

---

## 2. Key Architectural Lessons from Studied Systems

### 2.1 LLVM: Analysis vs Transformation Passes
LLVM structures its pipeline into pure, composable passes:
- **Analysis Passes**: Inspect the IR and produce immutable facts (e.g. dominator trees, loop bounds, dead code detection) without mutating the IR.
- **Transformation Passes**: Consume analysis facts and return a mutated, cleaner IR (e.g. dead code elimination, constant propagation).
- **Pass Manager**: Coordinates dependencies between passes and runs them sequentially until reaching a stable checkpoint.

*Application to AgentIR*: Implement a formal `PassManager` running passes like `DeadNodeEliminationPass`, `UnreachablePathPruningPass`, and `ToolSchemaNormalizationPass`.

### 2.2 Temporal: Deterministic Workflow Replay
Temporal guarantees that a workflow function produces the exact same sequence of commands on replay:
- Workflow code must be deterministic: no ambient timestamps, no random UUIDs, no unversioned network calls.
- Non-deterministic operations (calling an LLM, querying an external API) are isolated as discrete **Activities** or **Tools**.

*Application to AgentIR*: The AgentIR runtime and workflow graphs must have deterministic state transition tables with $O(1)$ dispatch.

### 2.3 W3C SCXML / XState: Transition Collision Resolution
In statecharts, if multiple conditional edges out of a state evaluate to true, non-determinism occurs unless strict priority ordering is enforced.

*Application to AgentIR*: AgentIR's `EdgeSpec` and graph validator must detect and resolve transition collisions deterministically using explicit evaluation order.

### 2.4 Google Pregel: Commutative & Associative Reducers
Pregel ensures deterministic state updates across supersteps by requiring reducers (like message appending or numerical aggregation) to be mathematically associative and commutative.

*Application to AgentIR*: `StateChannelSpec` validates that reducers (`append`, `replace`, `merge`) adhere to strict algebraic properties.

---

## 3. The 5 Deterministic Pillars for AgentIR

1. **Deterministic Hashing**: Canonical serialization where key reordering, whitespace, and list permutations produce identical SHA-256 digests.
2. **Compiler Passes**: Static symbolic transformation passes running in microseconds (`<1ms`) without external dependencies.
3. **Finite State Machine (FSM) Soundness**: Topological sorting, cycle classification (DAG vs Cyclic), dead-end detection, and reachability proofs.
4. **Strict Schema Conformance**: JSON Schema Draft 7 / 2020-12 parameter validation with default type coercion and boundary limits.
5. **No-LLM Invariant**: Every core compiler transformation, compatibility score, semantic diff, and validation rule must be 100% deterministic and reproducible.
