# ADR 0005: Security Model and Sandboxing

- **Status**: Accepted
- **Date**: 2026-09-16
- **Authors**: AgentIR Architecture Team

## Context

AgentIR ingests agent definitions from third-party repositories, user input, and external configuration files. These inputs may be untrusted or maliciously crafted. We must ensure AgentIR cannot be leveraged as an attack vector for arbitrary code execution, filesystem traversal, or credential exfiltration.

## Decision

1. **Safe YAML and JSON Parsing**:
   - Always use `yaml.safe_load()`. Disallow custom Python object tags (`!!python/object`).
   - Limit parsing depth and document size to mitigate Billion Laughs / YAML entity expansion attacks.

2. **No Arbitrary Code Execution**:
   - Zero use of `eval()`, `exec()`, or runtime compilation of untrusted code.
   - AST parsing is performed using Python's standard `ast` module with node visitor limits.

3. **Filesystem Path Traversal Protection**:
   - All input and output file paths must be resolved strictly relative to explicit base directories (`Path.resolve()` checks).
   - Attempts to write or read outside designated output roots raise `SecurityError`.

4. **Secret Scrubbing and Redaction**:
   - Standard regex and key-name scanners identify sensitive patterns (e.g. `api_key`, `secret`, `token`, `sk-[a-zA-Z0-9]{32,}`).
   - Secrets are redacted during logging and serialization (`[REDACTED]`).
   - Warnings are emitted if plain-text secrets are discovered in agent configurations.

## Alternatives Considered

- **Relying on user environment / containerization**:
  - *Rejected*: CLI tools must be secure by default on developer workstations and CI runners.

## Consequences

- **Positive**: Hardened toolchain suitable for automated CI/CD pipelines and enterprise multi-tenant environments.
- **Negative**: Strict path constraints require users to explicitly specify output directories when writing artifacts.
