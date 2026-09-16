# Research Note: OpenClaw

- **Subject**: OpenClaw Gateway & Multi-Platform Agent Runtime
- **Date Researched**: September 2026
- **Source Links**:
  - https://github.com/openclaw/openclaw

## 1. Observed Concepts & Architecture

OpenClaw is a modular, local-first agent gateway architecture designed for secure multi-platform operation:
- **Gateway Architecture**: Central coordinator managing message routing, protocol translation, and session lifecycles across diverse platforms (CLI, Discord, Slack, Webhooks).
- **Harness & Model Plugins**: Clean abstraction separating the core coordination engine from model providers and runtime execution harnesses.
- **Channel Abstraction**: Decouples incoming communication channels from internal agent representation, normalizing messages into standard payloads.
- **Local-First Security & Sandbox**:
  - Fine-grained permission envelopes for tools (filesystem access boundaries, network isolation, subprocess restrictions).
  - Explicit credential vaults preventing key leaks into prompts or agent context.

## 2. State & Memory Model

- Multi-tenant, session-partitioned state machines.
- State transitions are recorded as append-only event logs, ensuring tamper resistance and auditability.

## 3. Tool Model & Sandboxing

- Tools declare required permissions (e.g. `fs:read`, `net:outbound:domain`, `shell:execute`).
- Execution is mediated by a policy engine before tool code is invoked.

## 4. Adapter Implications for AgentIR

### What AgentIR Should Adopt:
- **Security Envelopes & Permissions**: In AgentIR's `Tool` model, add security metadata (`allowed_domains`, `filesystem_access`, `requires_sandbox`).
- **Clean Interface Boundary**: Ensure AgentIR domain models are strictly decoupled from I/O channels or gateway protocols.

### What AgentIR Should Explicitly NOT Adopt:
- Do not build network messaging gateways (Discord/Slack bots) into AgentIR.
- Keep AgentIR focused as a compiler toolchain and intermediate representation.
