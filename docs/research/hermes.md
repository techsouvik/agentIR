# Research Note: Hermes Agent

- **Subject**: NousResearch Hermes Agent
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/NousResearch/hermes-agent

## 1. Observed Concepts & Architecture

Hermes Agent by NousResearch is an autonomous agent runtime designed for self-improving and tool-augmented intelligence:
- **Autonomous Agent Loop**: Evaluates context, selects tools, parses responses, and manages iterative tool call chains.
- **Skills System**: Dynamic, modular capabilities loaded into the agent context on-demand, comprising instruction prompts, tool schemas, and reference resources.
- **Continuous Learning Loop**: Feedback collection mechanism that extracts lessons from successes and failures to update persistent memory.
- **Provider Abstraction**: Decoupled LLM client layer supporting OpenAI, Anthropic, vLLM, Ollama, and local open-weight endpoints.
- **Workspace Instructions**: Hierarchical instruction resolution (system defaults -> workspace instructions -> task-specific instructions).

## 2. Tool & Skill Abstraction

- Skills package tools together with specialized prompt snippets and operational guidelines.
- Tools feature explicit JSON Schema definitions with validation against inputs.

## 3. Memory & Learning Model

- Combines conversational memory with persistent skill/lesson stores.
- Allows retrospective reflection where summaries and corrections are persisted across agent sessions.

## 4. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **Hierarchical Instructions**: Support for `base_system_prompt`, `instructions_template`, and `workspace_context` in AgentIR's `Instructions` entity.
- **Skill / Capability Bundling**: Ability to group related tools and prompt augmentations into named capability sets.
- **Learning & Memory Configuration**: Declarative memory policies (`short_term`, `long_term`, `summary_window`).

### What AgentIR Should Explicitly NOT Adopt:
- Do not implement custom neural fine-tuning loops inside AgentIR.
- Keep AgentIR purely focused on representing and compiling agent specifications.
