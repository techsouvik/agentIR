# ADR 0004: Deterministic Canonicalization, Hashing, and Semantic Diff

- **Status**: Accepted
- **Date**: 2026-09-16
- **Authors**: AgentIR Architecture Team

## Context

To reliably compare agent definitions across framework boundaries, versions, or migration runs, AgentIR must provide reproducible serialization and explainable difference detection. Text-based line diffs (e.g. `git diff`) fail because trivial changes (key reordering, comments, whitespace, metadata) mask real behavioral changes.

## Decision

1. **Canonical Representation**:
   - Dictionaries and maps are recursively sorted by key.
   - Collections with set semantics (e.g. tools, handoff targets) are sorted by their stable identifier (`id` or `name`).
   - Floats are rounded to deterministic precision if needed.
   - Non-semantic metadata (source provenance, timestamps) is stripped when computing canonical hashes.

2. **Canonical Hashing**:
   - Compute SHA-256 digests over UTF-8 encoded canonical JSON strings generated via `orjson`.

3. **Semantic Diff Engine**:
   - Compare two canonical representations structured by domain entity:
     - `EQUIVALENT`: Exact semantic match (canonical hash identical).
     - `ADDITIVE`: New non-breaking capabilities, tools, or handoffs added.
     - `BEHAVIORAL`: Instructions, parameters, or models altered.
     - `BREAKING`: Tool parameter schemas removed or altered incompatibly; required state channels deleted; graph topology truncated.
     - `METADATA_ONLY`: Only provenance, labels, or descriptions changed.

## Alternatives Considered

- **Standard `diff -u` on raw YAML files**:
  - *Rejected*: Subject to key ordering and formatting differences.
- **Deepdiff library**:
  - *Rejected*: Adds third-party dependency; does not understand AgentIR domain semantics (e.g. breaking vs additive tool changes).

## Consequences

- **Positive**: Exact cache invalidation; verifiable round-tripping; clear, domain-aware diff reports for code reviews and migration audits.
