# Research Note: Google ADK (Agent Development Kit) & GenAI Agents

- **Subject**: Google GenAI / Agent Development Kit / Vertex AI Agent Builder
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/google-gemini/
  - https://cloud.google.com/vertex-ai/docs/agent-builder

## 1. Observed Concepts & Architecture

Google's agent ecosystem (spanning Vertex AI Agent Builder and Gemini Agent SDKs):
- **Agent Specification**: Goal-oriented definitions driven by Gemini's native multimodal capabilities and system instructions.
- **Tools & Extensions**:
  - OpenAPI-based tools (extensions).
  - Code execution sandbox (built-in Python sandbox).
  - Vertex Search datastores (grounding).
- **Playbooks / Flows**: Multi-step conversational task guidelines with step-by-step instructions, examples, and transition conditions to sub-playbooks.

## 2. Tool Abstraction

- Emphasizes OpenAPI 3.0 specs and Gemini Function Declarations (`name`, `description`, `parameters` matching JSON Schema subset).
- Grounding citations returned as first-class message metadata.

## 3. Playbook-Driven State & Routing

- Playbooks define natural language instructions combined with structured triggers for calling tools or transitioning between specialized playbooks.
- State is carried across playbook transitions.

## 4. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- OpenAPI 3.0 / JSON Schema tool definitions as the canonical tool format in AgentIR (`ToolInputSchema`).
- Grounding / search data source annotations in tools.

### What AgentIR Should Explicitly NOT Adopt:
- Do not couple AgentIR to Google Cloud IAM or Vertex AI resource URIs.
- Preserve tool schemas in standard JSON Schema rather than Google-proprietary protobuf variants.
