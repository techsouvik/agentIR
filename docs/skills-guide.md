# Modular Skills System Guide

In AgentIR, a **Skill** is a self-contained, modular package that bundles system prompt instructions, tool bindings, reference resources, and few-shot demonstration examples.

Inspired by skill architectures in Hermes Agent, OpenClaw, and Anthropic, Skills allow agents to dynamically acquire and exchange capabilities without monolithic prompt bloat.

---

## 1. The Skill Structure

A skill is defined by the `SkillSpec` domain entity:

```yaml
id: sql_expert
name: SQL Expert
description: Expert SQL query generation and schema analysis
instructions: |
  Always query the database schema before drafting multi-table joins.
  Prefer CTEs for readability on complex aggregations.
tools:
  - id: execute_sql
    name: Execute SQL
    description: Execute read-only SQL queries
    input_schema:
      type: object
      properties:
        query:
          type: string
          description: Valid SQL SELECT statement
      required:
        - query
resources:
  - name: db_schema
    uri: file:///schemas/enterprise_db.sql
    description: Database DDL definitions
    mime_type: application/sql
examples:
  - user_input: How many users signed up this week?
    expected_output: SELECT count(*) FROM users WHERE created_at >= date_trunc('week', current_date);
    tool_calls:
      - execute_sql
```

---

## 2. Using Skills in Agents

Skills can be attached to individual agents or shared across an entire manifest:

```yaml
name: Enterprise Analyst System
ir_version: "0.1.0"
shared_skills:
  - id: sql_expert
    name: SQL Expert
    ...

agents:
  - id: business_analyst
    name: Business Analyst
    model:
      provider: openai
      model_id: gpt-4o
    instructions:
      system_prompt: You provide strategic insights.
    skills:
      - id: sql_expert
        ...
```

---

## 3. Skill Resolution Lifecycle

When an agent executes with skills:
1. **Instruction Augmentation**: Skill instructions are appended as scoped guidelines to the agent's system prompt.
2. **Tool Activation**: Tools declared in the skill are bound to the agent turn.
3. **Resource Context**: URIs declared in `resources` can be resolved and injected into context.
4. **Few-Shot Demonstration**: Examples are formatted as demonstration messages to guide model adherence.
