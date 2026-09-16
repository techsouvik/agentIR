"""Model Context Protocol (MCP) tool and server adapter for AgentIR."""

import json
from pathlib import Path

import yaml

from agentir.adapters.base import FrameworkAdapter
from agentir.capabilities.status import CapabilitySupport, SemanticLossRisk, SupportLevel
from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AdapterError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.provenance import SourceProvenance
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec

MCP_CAPABILITIES = {
    "tool_calling": CapabilitySupport("tool_calling", SupportLevel.NATIVE, SemanticLossRisk.NONE),
    "structured_output": CapabilitySupport(
        "structured_output", SupportLevel.NATIVE, SemanticLossRisk.NONE
    ),
    "model_calling": CapabilitySupport(
        "model_calling",
        SupportLevel.ADAPTER,
        SemanticLossRisk.LOW,
        description="Delegated to client host application.",
    ),
    "sandboxing": CapabilitySupport(
        "sandboxing",
        SupportLevel.NATIVE,
        SemanticLossRisk.NONE,
        description="Isolated via stdio/SSE protocol boundary.",
    ),
}


class MCPAdapter(FrameworkAdapter):
    """Adapter for importing tools from and exporting tool servers to MCP."""

    framework_name: str = "mcp"
    framework_version_range: str = ">=0.1.0"
    adapter_version: str = "0.1.0"

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        return MCP_CAPABILITIES

    def can_import(self, source: Path | str) -> bool:
        path = Path(source)
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        return "tools" in content and ("inputSchema" in content or "mcp" in content)

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        path = Path(source).resolve()
        if not path.is_file():
            raise AdapterError(f"MCP source file not found: {path}")

        content = path.read_text(encoding="utf-8")
        try:
            data = json.loads(content) if path.suffix == ".json" else yaml.safe_load(content)
        except Exception as e:
            raise AdapterError(f"Failed to parse MCP document: {e}") from e

        if not isinstance(data, dict):
            raise AdapterError("MCP document must be a JSON/YAML object.")

        server_name = data.get("server_name", path.stem)
        raw_tools = data.get("tools", [])
        tools: list[ToolSpec] = []

        for rt in raw_tools:
            schema_data = rt.get("inputSchema", {})
            props_data = schema_data.get("properties", {})
            req_data = schema_data.get("required", [])

            properties: list[ToolParameterProperty] = []
            for p_name, p_info in props_data.items():
                properties.append(
                    ToolParameterProperty(
                        name=p_name,
                        type=p_info.get("type", "string"),
                        description=p_info.get("description", ""),
                        required=p_name in req_data,
                        default=p_info.get("default"),
                    )
                )

            tool_name = rt.get("name", "unnamed_tool")
            tools.append(
                ToolSpec(
                    id=f"mcp_{tool_name}",
                    name=tool_name,
                    description=rt.get("description", ""),
                    input_schema=ToolInputSchema(
                        properties=tuple(properties),
                        required=tuple(req_data),
                    ),
                    mcp_server=server_name,
                    mcp_tool_name=tool_name,
                )
            )

        agent = AgentSpec(
            id=f"{server_name}_agent",
            name=f"{server_name.title()} Agent",
            model=ModelSpec(provider="openai", model_id="gpt-4o"),
            instructions=InstructionsSpec(
                system_prompt=f"You have access to tools hosted on MCP server '{server_name}'."
            ),
            tools=tuple(tools),
            provenance=SourceProvenance(
                source_framework="mcp",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=server_name,
            agents=(agent,),
            shared_tools=tuple(tools),
            provenance=SourceProvenance(
                source_framework="mcp",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

    def export_manifest(
        self, manifest: AgentIRManifest, target_directory: Path | str
    ) -> list[Path]:
        out_dir = Path(target_directory).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        generated_files: list[Path] = []

        all_tools = list(manifest.shared_tools)
        for a in manifest.agents:
            all_tools.extend(a.tools)

        # 1. Generate mcp_server.py (FastMCP style)
        server_lines: list[str] = [
            "# Auto-generated by AgentIR",
            "# Target: Model Context Protocol (MCP) Server",
            "",
            "import asyncio",
            "import json",
            "import sys",
            "",
            "# Declared tools catalog for this server",
            "TOOLS = [",
        ]

        for t in all_tools:
            tool_dict = {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema.to_json_schema(),
            }
            server_lines.append(f"    {json.dumps(tool_dict)},")

        server_lines.extend(
            [
                "]",
                "",
                "def handle_list_tools() -> dict:",
                '    return {"tools": TOOLS}',
                "",
                "def handle_call_tool(name: str, arguments: dict) -> dict:",
                '    """Handler for MCP tool invocation."""',
                '    res = f"Executed {name} with {arguments}"',
                '    return {"content": [{"type": "text", "text": res}]}',
                "",
                'if __name__ == "__main__":',
                '    print(f"MCP Server initialized with {len(TOOLS)} tool(s).", file=sys.stderr)',
                '    print(json.dumps(handle_list_tools(), indent=2))',
            ]
        )

        server_py = out_dir / "mcp_server.py"
        server_py.write_text("\n".join(server_lines) + "\n", encoding="utf-8")
        generated_files.append(server_py)

        # 2. Generate claude_desktop_config.json snippet
        config_data = {
            "mcpServers": {
                manifest.name.lower().replace(" ", "_"): {
                    "command": "python",
                    "args": [str(server_py.resolve())],
                }
            }
        }
        config_path = out_dir / "claude_desktop_config.json"
        config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
        generated_files.append(config_path)

        return generated_files
