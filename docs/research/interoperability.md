# Research Note: Interoperability Standards (MCP, A2A, JSON Schema, OpenInference)

- **Subject**: Open Interoperability Protocols & Agent Interchange Standards
- **Date Researched**: September 2026
- **Source Links**:
  - Model Context Protocol (MCP): https://modelcontextprotocol.io
  - JSON Schema Specification: https://json-schema.org/
  - OpenInference / OpenTelemetry Semantic Conventions for Generative AI

## 1. Model Context Protocol (MCP)

### Overview
MCP standardizes how applications provide context to LLMs, exposing three primary primitives:
1. **Tools**: Executable functions callable by LLMs with defined JSON Schema parameters.
2. **Resources**: Static or dynamic data context (files, database records, API responses) that can be read by clients.
3. **Prompts**: Reusable prompt templates and workflows with predefined arguments.

### MCP in AgentIR
- AgentIR tools can represent both local callable tools and remote MCP servers (`mcp_server: str`, `mcp_tool_name: str`).
- Tool parameter schemas should natively conform to JSON Schema Draft 7 / Draft 2020-12, matching MCP standards.

## 2. Agent-to-Agent (A2A) Protocols

### Overview
A2A defines interaction semantics between heterogeneous agents:
- Capability discovery: Querying what skills/tools an agent possesses.
- Handoff requests: Delegating task context, constraints, and target deliverables.
- Structured replies: Returning standardized success/failure statuses and typed payload artifacts.

### A2A in AgentIR
- AgentIR's `Handoff` model specifies the target agent, input transformation, state transfer keys, and return policy.
- AgentIR's `Capability` taxonomy provides the exact vocabulary required for agents to advertise and negotiate compatible interactions.

## 3. Tool Interchange & JSON Schema

- Different frameworks use varying representations for tool definitions:
  - Pydantic models (LangChain, Agno)
  - Python type hints / docstrings (Agno, OpenAI Agents)
  - Raw JSON Schema dictionaries (OpenAI function calling, Anthropic tools, MCP)
- AgentIR standardizes on canonical `ToolInputSchema` that serializes cleanly to standard JSON Schema while retaining Python typing metadata where useful.

## 4. Tracing & Observability (OpenInference / OTel)

- Standardized span kinds: `AGENT`, `CHAIN`, `LLM`, `TOOL`, `RETRIEVER`.
- Standard attributes: `input.value`, `output.value`, `llm.token_count.prompt`, `llm.token_count.completion`.
- AgentIR preserves tracing metadata and lifecycle hook declarations without forcing a specific telemetry SDK.
