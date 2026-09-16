"""Agno framework adapter for AgentIR."""

import ast
from pathlib import Path

import yaml

from agentir.adapters.base import FrameworkAdapter
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import CapabilitySupport
from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AdapterError
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.memory import MemorySpec
from agentir.domain.model import ModelSpec
from agentir.domain.provenance import SourceProvenance
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec


class AgnoAdapter(FrameworkAdapter):
    """Adapter for importing from and exporting to Agno (formerly Phidata)."""

    framework_name: str = "agno"
    framework_version_range: str = ">=1.0.0,<2.0.0"
    adapter_version: str = "0.1.0"

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        return FRAMEWORK_CAPABILITY_MATRICES["agno"]

    def can_import(self, source: Path | str) -> bool:
        path = Path(source)
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json") and "framework" in content:
            try:
                data = yaml.safe_load(content)
                return isinstance(data, dict) and data.get("framework") == "agno"
            except Exception:
                return False
        return "from agno" in content or "import agno" in content or "Agent(" in content

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        path = Path(source).resolve()
        if not path.is_file():
            raise AdapterError(f"Agno source file not found: {path}")

        content = path.read_text(encoding="utf-8")
        is_markup = path.suffix in (".yaml", ".yml", ".json")
        has_keywords = "agents" in content or "instructions" in content
        if is_markup and has_keywords:
            return self._import_from_fixture(content, path)

        return self._import_from_python_ast(content, path)

    def _import_from_fixture(self, content: str, path: Path) -> AgentIRManifest:
        data = yaml.safe_load(content)
        agents: list[AgentSpec] = []

        agent_entries = data.get("agents") or [data]
        for item in agent_entries:
            tools: list[ToolSpec] = []
            for t_data in item.get("tools", []):
                props: list[ToolParameterProperty] = []
                for p in t_data.get("parameters", []):
                    props.append(
                        ToolParameterProperty(
                            name=p.get("name", "arg"),
                            type=p.get("type", "string"),
                            description=p.get("description", ""),
                            required=p.get("required", False),
                        )
                    )
                tools.append(
                    ToolSpec(
                        id=t_data.get("name", "tool"),
                        name=t_data.get("name", "tool"),
                        description=t_data.get("description", ""),
                        input_schema=ToolInputSchema(properties=tuple(props)),
                    )
                )

            m_data = item.get("model", {})
            model = ModelSpec(
                provider=m_data.get("provider", "openai"),
                model_id=m_data.get("model_id", "gpt-4o"),
                temperature=m_data.get("temperature", 0.7),
            )

            handoffs = [
                HandoffSpec(
                    target_agent_id=h.get("target"),
                    description=h.get("description", "Delegate task"),
                )
                for h in item.get("handoffs", [])
            ]

            agents.append(
                AgentSpec(
                    id=item.get("id", item.get("name", "agno_agent")),
                    name=item.get("name", "Agno Agent"),
                    model=model,
                    instructions=InstructionsSpec(
                        system_prompt=item.get("instructions", "You are an Agno agent.")
                    ),
                    tools=tuple(tools),
                    handoffs=tuple(handoffs),
                    memory=MemorySpec(memory_type="conversation_buffer"),
                    provenance=SourceProvenance(
                        source_framework="agno",
                        source_identifier=path.name,
                        source_file=str(path),
                    ),
                )
            )

        return AgentIRManifest(
            name=path.stem,
            agents=tuple(agents),
            provenance=SourceProvenance(
                source_framework="agno",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

    def _import_from_python_ast(self, content: str, path: Path) -> AgentIRManifest:
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            raise AdapterError(f"Failed to parse Agno Python AST: {e}") from e

        agent_name = "agno_agent"
        instructions = "You are a helpful assistant."
        model_id = "gpt-4o"
        provider = "openai"

        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                func_name = ""
                if isinstance(call.func, ast.Name):
                    func_name = call.func.id
                elif isinstance(call.func, ast.Attribute):
                    func_name = call.func.attr

                if func_name == "Agent":
                    for kw in call.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            agent_name = str(kw.value.value)
                        elif kw.arg == "instructions" and isinstance(kw.value, ast.Constant):
                            instructions = str(kw.value.value)

        agent = AgentSpec(
            id=agent_name.lower().replace(" ", "_"),
            name=agent_name,
            model=ModelSpec(provider=provider, model_id=model_id),
            instructions=InstructionsSpec(system_prompt=instructions),
            provenance=SourceProvenance(
                source_framework="agno",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=path.stem,
            agents=(agent,),
            provenance=SourceProvenance(
                source_framework="agno",
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

        code_lines: list[str] = [
            "# Auto-generated by AgentIR (https://github.com/agentir/agentir)",
            "# Target: Agno",
            "# Target version range: >=1.0.0,<2.0.0",
            "",
            "from agno.agent import Agent",
            "from agno.models.openai import OpenAIChat",
            "",
        ]

        # Generate Tools if present
        all_tools = manifest.shared_tools
        if manifest.agents:
            for a in manifest.agents:
                all_tools = (*all_tools, *a.tools)

        tool_names: list[str] = []
        for t in all_tools:
            fn_name = t.name.lower().replace(" ", "_")
            tool_names.append(fn_name)
            code_lines.extend(
                [
                    f"def {fn_name}() -> str:",
                    f'    """{t.description}"""',
                    f'    return "Executed {t.name}"',
                    "",
                ]
            )

        # Check persistent storage
        has_storage = any(
            a.memory and a.memory.persist_across_sessions for a in manifest.agents
        )
        if has_storage:
            code_lines.insert(6, "from agno.storage.agent.sqlite import SqliteAgentStorage")

        # Generate Agents
        tools_repr = f"[{', '.join(tool_names)}]" if tool_names else "[]"
        if manifest.agents:
            for _idx, a in enumerate(manifest.agents):
                var_name = f"agent_{a.id}" if len(manifest.agents) > 1 else "agent"
                agent_def = [
                    f"{var_name} = Agent(",
                    f'    name="{a.name}",',
                    f'    model=OpenAIChat(id="{a.model.model_id}"),',
                    f'    instructions="""{a.instructions.system_prompt}""",',
                    f"    tools={tools_repr},",
                ]
                if a.memory and a.memory.persist_across_sessions:
                    agent_def.append(
                        '    storage=SqliteAgentStorage(table_name="sessions"),'
                    )
                agent_def.extend(
                    [
                        "    markdown=True,",
                        ")",
                        "",
                    ]
                )
                code_lines.extend(agent_def)
        else:
            code_lines.extend(
                [
                    "agent = Agent(",
                    '    name="Default Agent",',
                    '    model=OpenAIChat(id="gpt-4o"),',
                    '    instructions="You are a helpful assistant.",',
                    "    markdown=True,",
                    ")",
                    "",
                ]
            )

        code_lines.extend(
            [
                'if __name__ == "__main__":',
                '    agent.print_response("Hello from AgentIR!")',
            ]
        )

        agent_py = out_dir / "agent.py"
        agent_py.write_text("\n".join(code_lines) + "\n", encoding="utf-8")
        generated_files.append(agent_py)

        # Generate requirements.txt
        reqs = out_dir / "requirements.txt"
        reqs.write_text("agno>=1.0.0\nopenai>=1.20.0\n", encoding="utf-8")
        generated_files.append(reqs)

        return generated_files
