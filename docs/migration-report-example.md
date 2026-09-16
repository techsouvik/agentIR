# Sample AgentIR Migration Audit Report

This is an annotated example of the audit report generated automatically by `agentir migrate` and `agentir.compiler.compile_migration()`.

```markdown
# AgentIR Migration Audit Report — Customer Support System

- **Source System**: Customer Support System (`0.1.0`)
- **Canonical Hash**: `321ee18dd2093544c4f69c50f94bcf346df7c91a53227fff3e171dd9148abb5a`
- **Target Framework**: `agno`
- **Compatibility Score**: **83.3%**
- **Migration Status**: SUCCESS (Forced)

## 1. Capabilities Summary

- **Total Required Capabilities**: 9
- **Native**: 7
- **Adapter Bridged**: 0
- **Emulated**: 1
- **Unsupported**: 1

### Native Matches
- `✓` **model_calling**: Natively supported.
- `✓` **multi_agent**: Natively supported.
- `✓` **persistent_state**: Natively supported.
- `✓` **routing**: Natively supported.
- `✓` **streaming**: Natively supported.
- `✓` **timeout**: Natively supported.
- `✓` **tool_calling**: Natively supported.

### Emulated Capabilities (Semantic Risk Warning)
- `⚠` **conditional_edges** (Risk: MEDIUM): Compiled into procedural Python branching inside an Agno Workflow.

### Unsupported Capabilities
- `✗` **checkpointing** (Risk: HIGH): Agno does not offer superstep graph time-travel checkpointing.

## 2. Generated Artifacts

- `agent.py`
- `requirements.txt`

## 3. Recommended Manual Actions

1. ACTION REQUIRED: Remove or manually re-architect checkpointing for agno.
2. Review emulation strategy for conditional_edges: Compiled into procedural Python branching inside an Agno Workflow.
```

The report provides deterministic, auditable evidence for engineering teams verifying migration fidelity.
