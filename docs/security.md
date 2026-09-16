# AgentIR Security Model & Threat Mitigation

## 1. Threat Vectors & Defenses

AgentIR is designed to safely ingest, analyze, and compile agent definitions from untrusted third-party repositories and external sources.

### 1.1 Arbitrary Code Execution (ACE) Defense
- **Risk**: Malicious Python files executing shell payloads during import or AST parsing.
- **Defense**:
  - Zero execution: AgentIR never calls `eval()`, `exec()`, or dynamic imports on user files.
  - Safe YAML: Uses `yaml.safe_load()`. Disallows Python constructor tags (`!!python/object`).

### 1.2 Denial of Service (DoS) & Payload Size Limits
- **Risk**: Billion Laughs entity expansion attacks or gigabyte-scale YAML payloads designed to exhaust memory.
- **Defense**:
  - Hard 10MB payload size limit enforced before parsing (`MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024`).
  - Safe parser settings preventing recursive reference amplification.

### 1.3 Path Traversal Protection
- **Risk**: Malicious output paths attempting to overwrite critical host files (e.g. `../../../../etc/passwd`).
- **Defense**:
  - All file inputs and output directories are strictly resolved using `Path.resolve()`.
  - Export commands create and write exclusively within designated target directories.

### 1.4 Secret Leakage Detection
- **Risk**: Hardcoded developer API keys (`sk-...`, Bearer tokens, passwords) accidentally committed into manifests.
- **Defense**:
  - Built-in regex scanners inspect system prompts, guidelines, and metadata during verification.
  - Flags potential credential exposure with severity `ERROR`.
  - Automatically redacts sensitive fields in debug logs.

## 2. CI/CD & Headless Operation
AgentIR is fully scriptable in automated pipelines:
- Returns non-zero exit codes on validation failures or blocked migrations.
- Supports `--json` for machine-to-machine event pipelines.
- Supports `--quiet` to suppress terminal formatting in headless runners.
