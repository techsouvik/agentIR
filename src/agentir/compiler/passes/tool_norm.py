"""Tool input schema normalization and sanitization pass."""

from agentir.compiler.passes.base import CompilerPass, PassResult
from agentir.domain.agent import AgentSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec

VALID_JSON_TYPES = frozenset({"string", "integer", "number", "boolean", "array", "object", "null"})


class ToolSchemaNormalizationPass(CompilerPass):
    """Normalizes and canonicalizes tool parameter schemas for deterministic evaluation."""

    @property
    def name(self) -> str:
        return "ToolSchemaNormalization"

    def run(self, manifest: AgentIRManifest) -> tuple[AgentIRManifest, PassResult]:
        mutations = 0
        messages: list[str] = []

        # 1. Normalize shared tools
        normalized_shared_tools: list[ToolSpec] = []
        for t in manifest.shared_tools:
            norm_t, tool_mutations = self._normalize_tool(t)
            normalized_shared_tools.append(norm_t)
            mutations += tool_mutations

        # 2. Normalize agent tools
        normalized_agents: list[AgentSpec] = []
        for a in manifest.agents:
            norm_agent_tools: list[ToolSpec] = []
            for t in a.tools:
                norm_t, tool_mutations = self._normalize_tool(t)
                norm_agent_tools.append(norm_t)
                mutations += tool_mutations

            if norm_agent_tools != list(a.tools):
                normalized_agents.append(
                    AgentSpec(
                        id=a.id,
                        name=a.name,
                        model=a.model,
                        instructions=a.instructions,
                        description=a.description,
                        tools=tuple(norm_agent_tools),
                        skills=a.skills,
                        handoffs=a.handoffs,
                        memory=a.memory,
                        state=a.state,
                        execution_policy=a.execution_policy,
                        output=a.output,
                        guards=a.guards,
                        metadata=a.metadata,
                        provenance=a.provenance,
                    )
                )
            else:
                normalized_agents.append(a)

        if mutations > 0:
            messages.append(f"Normalized {mutations} tool schema parameter(s).")
            new_manifest = AgentIRManifest(
                name=manifest.name,
                ir_version=manifest.ir_version,
                description=manifest.description,
                agents=tuple(normalized_agents),
                workflows=manifest.workflows,
                shared_tools=tuple(normalized_shared_tools),
                shared_skills=manifest.shared_skills,
                shared_state=manifest.shared_state,
                metadata=manifest.metadata,
                provenance=manifest.provenance,
            )
            return new_manifest, PassResult(
                pass_name=self.name,
                duration_micros=0.0,
                mutations_count=mutations,
                messages=tuple(messages),
            )

        return manifest, PassResult(
            pass_name=self.name,
            duration_micros=0.0,
            mutations_count=0,
            messages=("All tool schemas are strictly normalized; 0 mutations.",),
        )

    def _normalize_tool(self, tool: ToolSpec) -> tuple[ToolSpec, int]:
        mutations = 0
        schema = tool.input_schema

        prop_names = {p.name for p in schema.properties}
        normalized_props: list[ToolParameterProperty] = []

        for p in schema.properties:
            type_val = p.type.lower().strip() if p.type else "string"
            if type_val not in VALID_JSON_TYPES:
                type_val = "string"
                mutations += 1

            desc_val = p.description.strip()
            if not desc_val:
                desc_val = f"Parameter '{p.name}'."
                mutations += 1

            if type_val != p.type or desc_val != p.description:
                normalized_props.append(
                    ToolParameterProperty(
                        name=p.name,
                        type=type_val,
                        description=desc_val,
                        required=p.required,
                        default=p.default,
                        enum_values=p.enum_values,
                        items_type=p.items_type,
                    )
                )
            else:
                normalized_props.append(p)

        # Ensure required fields only reference declared properties
        valid_required = tuple(r for r in schema.required if r in prop_names)
        if len(valid_required) != len(schema.required):
            mutations += len(schema.required) - len(valid_required)

        if mutations > 0:
            norm_schema = ToolInputSchema(
                type=schema.type,
                properties=tuple(normalized_props),
                required=valid_required,
                additional_properties=schema.additional_properties,
            )
            return (
                ToolSpec(
                    id=tool.id,
                    name=tool.name,
                    description=tool.description,
                    input_schema=norm_schema,
                    is_pure=tool.is_pure,
                    requires_approval=tool.requires_approval,
                    timeout_seconds=tool.timeout_seconds,
                    permissions=tool.permissions,
                    mcp_server=tool.mcp_server,
                    mcp_tool_name=tool.mcp_tool_name,
                    return_direct=tool.return_direct,
                    handler_module=tool.handler_module,
                    handler_callable=tool.handler_callable,
                    metadata=tool.metadata,
                ),
                mutations,
            )

        return tool, 0
