# Research Note: OpenAI Agents SDK

- **Subject**: OpenAI Agents SDK (Swarm evolution & official Agents SDK)
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/openai/openai-agents-python
  - https://platform.openai.com/docs/guides/agents

## 1. Observed Concepts & Architecture

OpenAI's Agents SDK is centered on lightweight primitives for multi-agent coordination, handoffs, and deterministic guardrails:
- **Agent**:
  - `name`: string identifier.
  - `instructions`: string or callable `(context_variables) -> str`.
  - `model`: model identifier (e.g., `gpt-4o`, `gpt-4o-mini`).
  - `tools`: list of functions or tool definitions.
  - `handoffs`: list of target agents to which control can be transferred.
  - `guardrails`: input/output validation checks executed before and after agent turns.
- **Handoff**:
  - A first-class primitive: an agent returning a handoff function switches the active conversational agent to another agent, transferring conversation history and context variables.
- **Runner**:
  - Stateless execution engine: `Runner.run(agent, input=...)`.

## 2. Lifecycle & Execution Model

- Agent loop:
  1. Input provided with optional context variables.
  2. Input guardrails evaluated.
  3. LLM invoked with current agent instructions and available tools (including handoff tools).
  4. If tool call is a handoff, active agent changes; loop continues with the new agent.
  5. If regular tool call, tool executes, output appended, loop continues.
  6. When completion reached, output guardrails evaluated.
  7. Final result and updated context returned.

## 3. Tool & Handoff Abstraction

- Tools are standard Python functions with docstrings and type annotations.
- Handoffs are modeled either as functions returning another Agent or explicit `Handoff(target=..., condition=...)` objects.

## 4. Guardrails

- Pre-execution guardrails (e.g., PII detection, safety checks, prompt injection defense).
- Post-execution guardrails (e.g., hallucination check, output schema validation, tone compliance).
- Guardrails can abort, sanitize, or trigger fallback agents.

## 5. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **First-Class Handoff Primitive**: AgentIR must have a dedicated `Handoff` model (`target_agent_id`, `description`, `input_filter`, `transfer_state_keys`).
- **Guardrails**: AgentIR's `Guard` domain model (`name`, `stage: "input" | "output" | "tool"`, `rule_type`, `action_on_failure`).
- **Context Variables / Session State**: Explicit parameter injection into instructions.

### What AgentIR Should Explicitly NOT Adopt:
- Do not make the IR OpenAI-only; provider names and model IDs must remain framework-neutral.
- Do not require callable functions for instructions in the canonical serializable IR; represent parameterized prompt templates deterministically.
