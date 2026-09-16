"""Pydantic v2 schemas for AgentIR serialization, deserialization, and boundary validation."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.guard import GuardSpec
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.memory import MemorySpec
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.output import OutputSpec
from agentir.domain.policy import ExecutionPolicy
from agentir.domain.provenance import SourceProvenance
from agentir.domain.skill import SkillExample, SkillResource, SkillSpec
from agentir.domain.state import StateChannelSpec, StateSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec


class BaseSchema(BaseModel):
    """Base schema with strict validation config."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
    )


class SourceProvenanceSchema(BaseSchema):
    """Schema for source provenance tracking."""

    source_framework: str
    source_identifier: str
    source_file: str | None = None
    framework_version: str | None = None
    adapter_version: str | None = None
    imported_at: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> SourceProvenance:
        kwargs: dict[str, Any] = {
            "source_framework": self.source_framework,
            "source_identifier": self.source_identifier,
            "source_file": self.source_file,
            "framework_version": self.framework_version,
            "adapter_version": self.adapter_version,
            "metadata": dict(self.metadata),
        }
        if self.imported_at:
            kwargs["imported_at"] = self.imported_at
        return SourceProvenance(**kwargs)

    @classmethod
    def from_domain(cls, domain: SourceProvenance) -> "SourceProvenanceSchema":
        return cls(
            source_framework=domain.source_framework,
            source_identifier=domain.source_identifier,
            source_file=domain.source_file,
            framework_version=domain.framework_version,
            adapter_version=domain.adapter_version,
            imported_at=domain.imported_at,
            metadata=dict(domain.metadata),
        )


class ModelSpecSchema(BaseSchema):
    """Schema for model binding configuration."""

    provider: str
    model_id: str
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop_sequences: list[str] = Field(default_factory=list)
    reasoning_effort: str | None = None
    timeout_seconds: float | None = None
    configuration: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> ModelSpec:
        return ModelSpec(
            provider=self.provider,
            model_id=self.model_id,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            stop_sequences=tuple(self.stop_sequences),
            reasoning_effort=self.reasoning_effort,
            timeout_seconds=self.timeout_seconds,
            configuration=dict(self.configuration),
        )

    @classmethod
    def from_domain(cls, domain: ModelSpec) -> "ModelSpecSchema":
        return cls(
            provider=domain.provider,
            model_id=domain.model_id,
            temperature=domain.temperature,
            max_tokens=domain.max_tokens,
            top_p=domain.top_p,
            frequency_penalty=domain.frequency_penalty,
            presence_penalty=domain.presence_penalty,
            stop_sequences=list(domain.stop_sequences),
            reasoning_effort=domain.reasoning_effort,
            timeout_seconds=domain.timeout_seconds,
            configuration=dict(domain.configuration),
        )


class InstructionsSpecSchema(BaseSchema):
    """Schema for instructions and persona definition."""

    system_prompt: str
    persona: str | None = None
    role: str | None = None
    template_variables: list[str] = Field(default_factory=list)
    guidelines: list[str] = Field(default_factory=list)
    workspace_context: str | None = None

    def to_domain(self) -> InstructionsSpec:
        return InstructionsSpec(
            system_prompt=self.system_prompt,
            persona=self.persona,
            role=self.role,
            template_variables=tuple(self.template_variables),
            guidelines=tuple(self.guidelines),
            workspace_context=self.workspace_context,
        )

    @classmethod
    def from_domain(cls, domain: InstructionsSpec) -> "InstructionsSpecSchema":
        return cls(
            system_prompt=domain.system_prompt,
            persona=domain.persona,
            role=domain.role,
            template_variables=list(domain.template_variables),
            guidelines=list(domain.guidelines),
            workspace_context=domain.workspace_context,
        )


class ToolParameterPropertySchema(BaseSchema):
    """Schema for a single property of a tool input parameter."""

    name: str
    type: str
    description: str = ""
    required: bool = False
    default: Any | None = None
    enum_values: list[str] = Field(default_factory=list)
    items_type: str | None = None

    def to_domain(self) -> ToolParameterProperty:
        return ToolParameterProperty(
            name=self.name,
            type=self.type,
            description=self.description,
            required=self.required,
            default=self.default,
            enum_values=tuple(self.enum_values),
            items_type=self.items_type,
        )

    @classmethod
    def from_domain(cls, domain: ToolParameterProperty) -> "ToolParameterPropertySchema":
        return cls(
            name=domain.name,
            type=domain.type,
            description=domain.description,
            required=domain.required,
            default=domain.default,
            enum_values=list(domain.enum_values),
            items_type=domain.items_type,
        )


class ToolInputSchemaModel(BaseSchema):
    """Schema for tool JSON Schema input specification."""

    type: str = "object"
    properties: list[ToolParameterPropertySchema] = Field(default_factory=list)
    required: list[str] = Field(default_factory=list)
    additional_properties: bool = False

    def to_domain(self) -> ToolInputSchema:
        return ToolInputSchema(
            type=self.type,
            properties=tuple(p.to_domain() for p in self.properties),
            required=tuple(self.required),
            additional_properties=self.additional_properties,
        )

    @classmethod
    def from_domain(cls, domain: ToolInputSchema) -> "ToolInputSchemaModel":
        return cls(
            type=domain.type,
            properties=[ToolParameterPropertySchema.from_domain(p) for p in domain.properties],
            required=list(domain.required),
            additional_properties=domain.additional_properties,
        )


class ToolSpecSchema(BaseSchema):
    """Schema for tool specifications."""

    id: str
    name: str
    description: str
    input_schema: ToolInputSchemaModel = Field(default_factory=ToolInputSchemaModel)
    is_pure: bool = False
    requires_approval: bool = False
    timeout_seconds: float | None = None
    permissions: list[str] = Field(default_factory=list)
    mcp_server: str | None = None
    mcp_tool_name: str | None = None
    return_direct: bool = False
    handler_module: str | None = None
    handler_callable: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> ToolSpec:
        return ToolSpec(
            id=self.id,
            name=self.name,
            description=self.description,
            input_schema=self.input_schema.to_domain(),
            is_pure=self.is_pure,
            requires_approval=self.requires_approval,
            timeout_seconds=self.timeout_seconds,
            permissions=tuple(self.permissions),
            mcp_server=self.mcp_server,
            mcp_tool_name=self.mcp_tool_name,
            return_direct=self.return_direct,
            handler_module=self.handler_module,
            handler_callable=self.handler_callable,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_domain(cls, domain: ToolSpec) -> "ToolSpecSchema":
        return cls(
            id=domain.id,
            name=domain.name,
            description=domain.description,
            input_schema=ToolInputSchemaModel.from_domain(domain.input_schema),
            is_pure=domain.is_pure,
            requires_approval=domain.requires_approval,
            timeout_seconds=domain.timeout_seconds,
            permissions=list(domain.permissions),
            mcp_server=domain.mcp_server,
            mcp_tool_name=domain.mcp_tool_name,
            return_direct=domain.return_direct,
            handler_module=domain.handler_module,
            handler_callable=domain.handler_callable,
            metadata=dict(domain.metadata),
        )


class SkillResourceSchema(BaseSchema):
    """Schema for skill-attached resources."""

    name: str
    uri: str
    description: str = ""
    mime_type: str = "text/plain"

    def to_domain(self) -> SkillResource:
        return SkillResource(
            name=self.name,
            uri=self.uri,
            description=self.description,
            mime_type=self.mime_type,
        )

    @classmethod
    def from_domain(cls, domain: SkillResource) -> "SkillResourceSchema":
        return cls(
            name=domain.name,
            uri=domain.uri,
            description=domain.description,
            mime_type=domain.mime_type,
        )


class SkillExampleSchema(BaseSchema):
    """Schema for skill demonstration examples."""

    user_input: str
    expected_output: str
    tool_calls: list[str] = Field(default_factory=list)

    def to_domain(self) -> SkillExample:
        return SkillExample(
            user_input=self.user_input,
            expected_output=self.expected_output,
            tool_calls=tuple(self.tool_calls),
        )

    @classmethod
    def from_domain(cls, domain: SkillExample) -> "SkillExampleSchema":
        return cls(
            user_input=domain.user_input,
            expected_output=domain.expected_output,
            tool_calls=list(domain.tool_calls),
        )


class SkillSpecSchema(BaseSchema):
    """Schema for modular skill packages."""

    id: str
    name: str
    description: str
    instructions: str
    tools: list[ToolSpecSchema] = Field(default_factory=list)
    resources: list[SkillResourceSchema] = Field(default_factory=list)
    examples: list[SkillExampleSchema] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> SkillSpec:
        return SkillSpec(
            id=self.id,
            name=self.name,
            description=self.description,
            instructions=self.instructions,
            tools=tuple(t.to_domain() for t in self.tools),
            resources=tuple(r.to_domain() for r in self.resources),
            examples=tuple(e.to_domain() for e in self.examples),
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_domain(cls, domain: SkillSpec) -> "SkillSpecSchema":
        return cls(
            id=domain.id,
            name=domain.name,
            description=domain.description,
            instructions=domain.instructions,
            tools=[ToolSpecSchema.from_domain(t) for t in domain.tools],
            resources=[SkillResourceSchema.from_domain(r) for r in domain.resources],
            examples=[SkillExampleSchema.from_domain(e) for e in domain.examples],
            metadata=dict(domain.metadata),
        )


class MemorySpecSchema(BaseSchema):
    """Schema for memory configuration."""

    memory_type: str = "conversation_buffer"
    max_messages: int | None = 50
    summary_window: int | None = None
    vector_collection: str | None = None
    persist_across_sessions: bool = False
    storage_backend: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> MemorySpec:
        return MemorySpec(
            memory_type=self.memory_type,
            max_messages=self.max_messages,
            summary_window=self.summary_window,
            vector_collection=self.vector_collection,
            persist_across_sessions=self.persist_across_sessions,
            storage_backend=self.storage_backend,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_domain(cls, domain: MemorySpec) -> "MemorySpecSchema":
        return cls(
            memory_type=domain.memory_type,
            max_messages=domain.max_messages,
            summary_window=domain.summary_window,
            vector_collection=domain.vector_collection,
            persist_across_sessions=domain.persist_across_sessions,
            storage_backend=domain.storage_backend,
            metadata=dict(domain.metadata),
        )


class StateChannelSpecSchema(BaseSchema):
    """Schema for an individual state channel."""

    key: str
    type_name: str
    reducer: str = "replace"
    description: str = ""
    default_value: str | None = None

    def to_domain(self) -> StateChannelSpec:
        return StateChannelSpec(
            key=self.key,
            type_name=self.type_name,
            reducer=self.reducer,
            description=self.description,
            default_value=self.default_value,
        )

    @classmethod
    def from_domain(cls, domain: StateChannelSpec) -> "StateChannelSpecSchema":
        return cls(
            key=domain.key,
            type_name=domain.type_name,
            reducer=domain.reducer,
            description=domain.description,
            default_value=domain.default_value,
        )


class StateSpecSchema(BaseSchema):
    """Schema for a state model."""

    schema_name: str
    channels: list[StateChannelSpecSchema] = Field(default_factory=list)
    description: str = ""

    def to_domain(self) -> StateSpec:
        return StateSpec(
            schema_name=self.schema_name,
            channels=tuple(c.to_domain() for c in self.channels),
            description=self.description,
        )

    @classmethod
    def from_domain(cls, domain: StateSpec) -> "StateSpecSchema":
        return cls(
            schema_name=domain.schema_name,
            channels=[StateChannelSpecSchema.from_domain(c) for c in domain.channels],
            description=domain.description,
        )


class ExecutionPolicySchema(BaseSchema):
    """Schema for execution limits and runtime control policies."""

    max_turns: int | None = 25
    timeout_seconds: float | None = 300.0
    retry_limit: int = 0
    retry_delay_seconds: float = 1.0
    allow_delegation: bool = True
    requires_human_approval: bool = False
    interrupt_before_nodes: list[str] = Field(default_factory=list)
    interrupt_after_nodes: list[str] = Field(default_factory=list)
    parallel_execution: bool = False
    streaming: bool = False

    def to_domain(self) -> ExecutionPolicy:
        return ExecutionPolicy(
            max_turns=self.max_turns,
            timeout_seconds=self.timeout_seconds,
            retry_limit=self.retry_limit,
            retry_delay_seconds=self.retry_delay_seconds,
            allow_delegation=self.allow_delegation,
            requires_human_approval=self.requires_human_approval,
            interrupt_before_nodes=tuple(self.interrupt_before_nodes),
            interrupt_after_nodes=tuple(self.interrupt_after_nodes),
            parallel_execution=self.parallel_execution,
            streaming=self.streaming,
        )

    @classmethod
    def from_domain(cls, domain: ExecutionPolicy) -> "ExecutionPolicySchema":
        return cls(
            max_turns=domain.max_turns,
            timeout_seconds=domain.timeout_seconds,
            retry_limit=domain.retry_limit,
            retry_delay_seconds=domain.retry_delay_seconds,
            allow_delegation=domain.allow_delegation,
            requires_human_approval=domain.requires_human_approval,
            interrupt_before_nodes=list(domain.interrupt_before_nodes),
            interrupt_after_nodes=list(domain.interrupt_after_nodes),
            parallel_execution=domain.parallel_execution,
            streaming=domain.streaming,
        )


class OutputSpecSchema(BaseSchema):
    """Schema for structured output specification."""

    format: str = "text"
    schema_definition: ToolInputSchemaModel | None = None
    pydantic_class_name: str | None = None
    require_valid_json: bool = False
    description: str = ""
    json_schema_dict: dict[str, Any] | None = None

    def to_domain(self) -> OutputSpec:
        return OutputSpec(
            format=self.format,
            schema_definition=self.schema_definition.to_domain()
            if self.schema_definition
            else None,
            pydantic_class_name=self.pydantic_class_name,
            require_valid_json=self.require_valid_json,
            description=self.description,
            json_schema_dict=dict(self.json_schema_dict) if self.json_schema_dict else None,
        )

    @classmethod
    def from_domain(cls, domain: OutputSpec) -> "OutputSpecSchema":
        return cls(
            format=domain.format,
            schema_definition=ToolInputSchemaModel.from_domain(domain.schema_definition)
            if domain.schema_definition
            else None,
            pydantic_class_name=domain.pydantic_class_name,
            require_valid_json=domain.require_valid_json,
            description=domain.description,
            json_schema_dict=dict(domain.json_schema_dict) if domain.json_schema_dict else None,
        )


class HandoffSpecSchema(BaseSchema):
    """Schema for handoff / delegation specification."""

    target_agent_id: str
    description: str
    condition: str | None = None
    transfer_state_keys: list[str] = Field(default_factory=list)
    return_to_caller: bool = False

    def to_domain(self) -> HandoffSpec:
        return HandoffSpec(
            target_agent_id=self.target_agent_id,
            description=self.description,
            condition=self.condition,
            transfer_state_keys=tuple(self.transfer_state_keys),
            return_to_caller=self.return_to_caller,
        )

    @classmethod
    def from_domain(cls, domain: HandoffSpec) -> "HandoffSpecSchema":
        return cls(
            target_agent_id=domain.target_agent_id,
            description=domain.description,
            condition=domain.condition,
            transfer_state_keys=list(domain.transfer_state_keys),
            return_to_caller=domain.return_to_caller,
        )


class GuardSpecSchema(BaseSchema):
    """Schema for guardrails and safety rules."""

    name: str
    stage: str
    rule_type: str
    pattern_or_rule: str
    action_on_failure: str = "abort"
    fallback_target: str | None = None
    description: str = ""

    def to_domain(self) -> GuardSpec:
        return GuardSpec(
            name=self.name,
            stage=self.stage,
            rule_type=self.rule_type,
            pattern_or_rule=self.pattern_or_rule,
            action_on_failure=self.action_on_failure,
            fallback_target=self.fallback_target,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, domain: GuardSpec) -> "GuardSpecSchema":
        return cls(
            name=domain.name,
            stage=domain.stage,
            rule_type=domain.rule_type,
            pattern_or_rule=domain.pattern_or_rule,
            action_on_failure=domain.action_on_failure,
            fallback_target=domain.fallback_target,
            description=domain.description,
        )


class NodeSpecSchema(BaseSchema):
    """Schema for workflow graph nodes."""

    id: str
    type: str
    name: str
    agent_id: str | None = None
    tool_id: str | None = None
    handler_name: str | None = None
    description: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_domain(self) -> NodeSpec:
        return NodeSpec(
            id=self.id,
            type=self.type,
            name=self.name,
            agent_id=self.agent_id,
            tool_id=self.tool_id,
            handler_name=self.handler_name,
            description=self.description,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_domain(cls, domain: NodeSpec) -> "NodeSpecSchema":
        return cls(
            id=domain.id,
            type=domain.type,
            name=domain.name,
            agent_id=domain.agent_id,
            tool_id=domain.tool_id,
            handler_name=domain.handler_name,
            description=domain.description,
            metadata=dict(domain.metadata),
        )


class EdgeSpecSchema(BaseSchema):
    """Schema for workflow graph edges."""

    source_node_id: str
    target_node_id: str | None = None
    is_conditional: bool = False
    condition_expression: str | None = None
    router_callable: str | None = None
    path_map: dict[str, str] = Field(default_factory=dict)
    description: str = ""

    def to_domain(self) -> EdgeSpec:
        return EdgeSpec(
            source_node_id=self.source_node_id,
            target_node_id=self.target_node_id,
            is_conditional=self.is_conditional,
            condition_expression=self.condition_expression,
            router_callable=self.router_callable,
            path_map=dict(self.path_map),
            description=self.description,
        )

    @classmethod
    def from_domain(cls, domain: EdgeSpec) -> "EdgeSpecSchema":
        return cls(
            source_node_id=domain.source_node_id,
            target_node_id=domain.target_node_id,
            is_conditional=domain.is_conditional,
            condition_expression=domain.condition_expression,
            router_callable=domain.router_callable,
            path_map=dict(domain.path_map),
            description=domain.description,
        )


class WorkflowSpecSchema(BaseSchema):
    """Schema for workflow specifications."""

    id: str
    name: str
    entry_node_id: str
    nodes: list[NodeSpecSchema] = Field(default_factory=list)
    edges: list[EdgeSpecSchema] = Field(default_factory=list)
    finish_node_ids: list[str] = Field(default_factory=list)
    state: StateSpecSchema | None = None
    execution_policy: ExecutionPolicySchema | None = None
    description: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
    provenance: SourceProvenanceSchema | None = None

    def to_domain(self) -> WorkflowSpec:
        return WorkflowSpec(
            id=self.id,
            name=self.name,
            entry_node_id=self.entry_node_id,
            nodes=tuple(n.to_domain() for n in self.nodes),
            edges=tuple(e.to_domain() for e in self.edges),
            finish_node_ids=tuple(self.finish_node_ids),
            state=self.state.to_domain() if self.state else None,
            execution_policy=self.execution_policy.to_domain()
            if self.execution_policy
            else None,
            description=self.description,
            metadata=dict(self.metadata),
            provenance=self.provenance.to_domain() if self.provenance else None,
        )

    @classmethod
    def from_domain(cls, domain: WorkflowSpec) -> "WorkflowSpecSchema":
        return cls(
            id=domain.id,
            name=domain.name,
            entry_node_id=domain.entry_node_id,
            nodes=[NodeSpecSchema.from_domain(n) for n in domain.nodes],
            edges=[EdgeSpecSchema.from_domain(e) for e in domain.edges],
            finish_node_ids=list(domain.finish_node_ids),
            state=StateSpecSchema.from_domain(domain.state) if domain.state else None,
            execution_policy=ExecutionPolicySchema.from_domain(domain.execution_policy)
            if domain.execution_policy
            else None,
            description=domain.description,
            metadata=dict(domain.metadata),
            provenance=SourceProvenanceSchema.from_domain(domain.provenance)
            if domain.provenance
            else None,
        )


class AgentSpecSchema(BaseSchema):
    """Schema for Agent specifications."""

    id: str
    name: str
    model: ModelSpecSchema
    instructions: InstructionsSpecSchema
    description: str = ""
    tools: list[ToolSpecSchema] = Field(default_factory=list)
    skills: list[SkillSpecSchema] = Field(default_factory=list)
    handoffs: list[HandoffSpecSchema] = Field(default_factory=list)
    memory: MemorySpecSchema | None = None
    state: StateSpecSchema | None = None
    execution_policy: ExecutionPolicySchema = Field(default_factory=ExecutionPolicySchema)
    output: OutputSpecSchema | None = None
    guards: list[GuardSpecSchema] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    provenance: SourceProvenanceSchema | None = None

    def to_domain(self) -> AgentSpec:
        return AgentSpec(
            id=self.id,
            name=self.name,
            model=self.model.to_domain(),
            instructions=self.instructions.to_domain(),
            description=self.description,
            tools=tuple(t.to_domain() for t in self.tools),
            skills=tuple(s.to_domain() for s in self.skills),
            handoffs=tuple(h.to_domain() for h in self.handoffs),
            memory=self.memory.to_domain() if self.memory else None,
            state=self.state.to_domain() if self.state else None,
            execution_policy=self.execution_policy.to_domain(),
            output=self.output.to_domain() if self.output else None,
            guards=tuple(g.to_domain() for g in self.guards),
            metadata=dict(self.metadata),
            provenance=self.provenance.to_domain() if self.provenance else None,
        )

    @classmethod
    def from_domain(cls, domain: AgentSpec) -> "AgentSpecSchema":
        return cls(
            id=domain.id,
            name=domain.name,
            model=ModelSpecSchema.from_domain(domain.model),
            instructions=InstructionsSpecSchema.from_domain(domain.instructions),
            description=domain.description,
            tools=[ToolSpecSchema.from_domain(t) for t in domain.tools],
            skills=[SkillSpecSchema.from_domain(s) for s in domain.skills],
            handoffs=[HandoffSpecSchema.from_domain(h) for h in domain.handoffs],
            memory=MemorySpecSchema.from_domain(domain.memory) if domain.memory else None,
            state=StateSpecSchema.from_domain(domain.state) if domain.state else None,
            execution_policy=ExecutionPolicySchema.from_domain(domain.execution_policy),
            output=OutputSpecSchema.from_domain(domain.output) if domain.output else None,
            guards=[GuardSpecSchema.from_domain(g) for g in domain.guards],
            metadata=dict(domain.metadata),
            provenance=SourceProvenanceSchema.from_domain(domain.provenance)
            if domain.provenance
            else None,
        )


class AgentIRManifestSchema(BaseSchema):
    """Schema for root AgentIR manifest."""

    ir_version: str = "0.1.0"
    name: str
    description: str = ""
    agents: list[AgentSpecSchema] = Field(default_factory=list)
    workflows: list[WorkflowSpecSchema] = Field(default_factory=list)
    shared_tools: list[ToolSpecSchema] = Field(default_factory=list)
    shared_skills: list[SkillSpecSchema] = Field(default_factory=list)
    shared_state: StateSpecSchema | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    provenance: SourceProvenanceSchema | None = None

    def to_domain(self) -> AgentIRManifest:
        manifest = AgentIRManifest(
            name=self.name,
            ir_version=self.ir_version,
            description=self.description,
            agents=tuple(a.to_domain() for a in self.agents),
            workflows=tuple(w.to_domain() for w in self.workflows),
            shared_tools=tuple(t.to_domain() for t in self.shared_tools),
            shared_skills=tuple(s.to_domain() for s in self.shared_skills),
            shared_state=self.shared_state.to_domain() if self.shared_state else None,
            metadata=dict(self.metadata),
            provenance=self.provenance.to_domain() if self.provenance else None,
        )
        manifest.validate_invariants()
        return manifest

    @classmethod
    def from_domain(cls, domain: AgentIRManifest) -> "AgentIRManifestSchema":
        return cls(
            name=domain.name,
            ir_version=domain.ir_version,
            description=domain.description,
            agents=[AgentSpecSchema.from_domain(a) for a in domain.agents],
            workflows=[WorkflowSpecSchema.from_domain(w) for w in domain.workflows],
            shared_tools=[ToolSpecSchema.from_domain(t) for t in domain.shared_tools],
            shared_skills=[SkillSpecSchema.from_domain(s) for s in domain.shared_skills],
            shared_state=StateSpecSchema.from_domain(domain.shared_state)
            if domain.shared_state
            else None,
            metadata=dict(domain.metadata),
            provenance=SourceProvenanceSchema.from_domain(domain.provenance)
            if domain.provenance
            else None,
        )
