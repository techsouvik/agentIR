# Deterministic Runtime Simulation Guide

AgentIR includes a lightweight, deterministic simulation engine (`agentir.runtime.DeterministicRuntime`) that allows running, testing, and verifying agent workflows locally **without calling external LLMs or requiring API keys**.

---

## 1. Why Offline Simulation?

1. **Continuous Integration (CI/CD)**: Test agent workflows, tool calling logic, and graph transitions deterministically on every git commit without API expenses or rate limits.
2. **Safety & Guardrail Testing**: Verify that input guardrails abort malicious inputs or passwords before deploying to production.
3. **Graph Soundness**: Walk computational graphs, conditional edges, and handoff chains to ensure no execution loops stall or crash.

---

## 2. Using `agentir run` via CLI

Run a local dry-run simulation:

```bash
agentir run examples/customer_support_langgraph.yaml --input "Need refund for order #999"
```

Output:
```text
✓ Simulation completed! Status: SUCCESS
Final output: Completed simulation.
Total steps: 10
```

### JSON Execution Trace

Pass `--json` to inspect every turn, node execution, and state snapshot:

```bash
agentir run examples/customer_support_langgraph.yaml -i "Track order #123" --json
```

```json
{
  "success": true,
  "final_output": "Completed simulation.",
  "turn_count": 10,
  "halt_reason": null,
  "final_state": {
    "messages": [
      {
        "role": "user",
        "content": "Track order #123"
      }
    ]
  },
  "steps": [
    {
      "turn": 1,
      "agent_id": "support_agent",
      "action": "reasoning",
      "node_id": "triage_node",
      "input": "Track order #123",
      "output": "Node 'Triage Turn' executed."
    },
    {
      "turn": 2,
      "agent_id": "graph_runner",
      "action": "tool_call",
      "node_id": "tool_node",
      "input": "Track order #123",
      "output": "Mock result for lookup_order"
    }
  ]
}
```

---

## 3. Programmatic Usage in Python

You can also use the runtime directly in unit tests:

```python
from agentir.schema.serializer import load_manifest_from_file
from agentir.runtime.engine import DeterministicRuntime

manifest = load_manifest_from_file("my_agent.yaml")
runtime = DeterministicRuntime()

result = runtime.run(
    manifest=manifest,
    user_input="Hello world",
    mock_tool_responses={"Lookup Order": {"status": "shipped"}},
)

assert result.success is True
assert len(result.steps) > 0
```
