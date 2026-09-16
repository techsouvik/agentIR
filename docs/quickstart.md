# 5-Minute Quickstart Tutorial

This hands-on walkthrough guides you through creating, inspecting, checking, simulating, and compiling an agent using AgentIR.

---

## 1. Prerequisites

Ensure Python 3.12+ and `uv` or `pip` are installed:

```bash
uv pip install agentir
# or pip install agentir
```

Verify your environment:

```bash
agentir doctor
```

---

## 2. Scaffold a New Agent Manifest

Generate a starter manifest equipped with a sample tool:

```bash
agentir init weather_agent --template tools -o agentir.yaml
```

Inspect the generated `agentir.yaml`:

```yaml
name: weather_agent
ir_version: 0.1.0
agents:
  - id: weather_agent_agent
    name: Weather Agent
    model:
      provider: openai
      model_id: gpt-4o
      temperature: 0.7
    instructions:
      system_prompt: You are weather_agent, a helpful autonomous AI agent.
      guidelines:
        - Be concise
        - Ensure accuracy
    tools:
      - id: search_tool
        name: Search Tool
        description: Search documentation and web content
        input_schema:
          type: object
          properties:
            - name: query
              type: string
              required: true
          required:
            - query
```

---

## 3. Inspect Structure & Canonical Hash

```bash
agentir inspect agentir.yaml
```

AgentIR computes a deterministic SHA-256 hash over the canonical representation. Notice that reordering fields in the YAML does not alter this hash.

---

## 4. Test Compatibility Before Migration

Before committing to a target framework, verify whether it natively supports all features:

```bash
agentir check agentir.yaml --target agno
agentir check agentir.yaml --target langgraph
```

You will see an exact breakdown of `NATIVE`, `ADAPTER`, `EMULATED`, and `UNSUPPORTED` capabilities with actionable recommendations.

---

## 5. Offline Dry-Run Simulation

Simulate agent execution locally without external API keys:

```bash
agentir run agentir.yaml --input "What is the forecast in Seattle?"
```

Output:
```text
✓ Simulation completed! Status: SUCCESS
Final output: Simulated response from Weather Agent for: What is the forecast in Seattle?
Total steps: 2
```

---

## 6. Compile to Target Framework

Export your agent into native, runnable Python code for Agno:

```bash
agentir export agentir.yaml --target agno -o ./agno_project
```

Look at `./agno_project/agent.py`:
- Contains idiomatic `from agno.agent import Agent, OpenAIChat`.
- Ready to execute directly in production without any AgentIR dependencies!
