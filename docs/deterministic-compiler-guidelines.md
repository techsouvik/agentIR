# AgentIR Deterministic Compiler Guidelines

These guidelines are mandatory for all core compiler, optimization, and analysis components in AgentIR.

---

## 1. The Zero-LLM Invariant

**Rule 1.1**: The AgentIR compiler pipeline (parsing, canonicalization, optimization passes, capability analysis, compatibility grading, semantic diff, and code generation) **MUST NEVER invoke or rely upon an LLM**.

**Rationale**: Compilers must be fast, reproducible, and verifiable. A compiler that calls an LLM introduces non-deterministic syntax mutations, latency ($>1000\text{ms}$ vs $<1\text{ms}$), variable cost, and un-testable failure modes.

---

## 2. Invariant: Pass Idempotency

**Rule 2.1**: Every compiler optimization pass $P$ must be mathematically **idempotent**:

$$P(P(M)) = P(M)$$

Applying a pass once achieves the optimized canonical state. Applying it a second time produces zero additional mutations and yields the exact same canonical hash.

---

## 3. Algorithmic Complexity Budgets

To ensure extreme speed ($>10,000\text{ ops/sec}$), core algorithms must observe strict complexity limits:

| Operation | Maximum Allowed Complexity | Notes |
| :--- | :--- | :--- |
| **Canonical Hashing** | $O(N \log N)$ | Log factor from sorting keys and collection identifiers. |
| **Graph Reachability** | $O(V + E)$ | Breadth-first or depth-first traversal. |
| **Cycle Classification** | $O(V + E)$ | Tarjan's or Kosaraju's strongly connected components algorithm. |
| **State Machine Dispatch** | $O(1)$ | Hash table lookup on current node and state branch keys. |
| **Semantic Diffing** | $O(N_1 \log N_1 + N_2 \log N_2)$| Key alignment and recursive value comparison. |
| **Pass Execution** | $O(V + E + T)$ | Linear in nodes, edges, and tools. |

---

## 4. Deterministic Canonical Ordering

**Rule 4.1**: All collections with set semantics must be deterministically sorted before computing hashes or serialization:
- **Agents**: Sorted by `agent.id`.
- **Workflows**: Sorted by `workflow.id`.
- **Nodes**: Sorted by `node.id`.
- **Edges**: Sorted by `(edge.source_node_id, edge.target_node_id or '')`.
- **Tools**: Sorted by `tool.id`.
- **Tool Properties**: Sorted by `property.name`.
- **Guards**: Sorted by `guard.name`.
- **Handoffs**: Sorted by `handoff.target_agent_id`.
- **State Channels**: Sorted by `channel.key`.

**Rule 4.2**: Ephemeral metadata (`imported_at`, execution timestamps) must be scrubbed from canonical dictionary representations to preserve semantic hash identity.

---

## 5. Transition Collision Resolution (FSM Soundness)

**Rule 5.1**: In conditional edges, branches must evaluate in declared order with a guaranteed fallback:
1. Branches in `EdgeSpec.path_map` evaluate deterministically.
2. If no condition matches, graph traversal transitions to `default` or `END`.
3. The compiler pass detects and flags overlapping or ambiguous branch keys as warnings.

---

## 6. Immutable Value Objects

**Rule 6.1**: All domain objects must be immutable (`@dataclass(frozen=True, slots=True)`).
Compiler passes must never mutate domain objects in-place; they return new instances, ensuring pure functional transformations and safe concurrency.
