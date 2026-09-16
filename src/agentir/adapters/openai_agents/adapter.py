"""OpenAI Agents SDK adapter for AgentIR."""

import ast
from pathlib import Path

import yaml

from agentir.adapters.base import FrameworkAdapter
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import CapabilitySupport
from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AdapterError
from agentir.domain.guard import GuardSpec
from agentir.domain.handoff import HandoffSpec
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.provenance import SourceProvenance
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec


class OpenAIAgentsAdapter(FrameworkAdapter):
    """Adapter for importing from and exporting to OpenAI Agents SDK."""

    framework_name: str = "openai_agents"
    framework_version_range: str = ">=0.1.0,<1.0.0"
    adapter_version: str = "0.1.0"

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        return FRAMEWORK_CAPABILITY_MATRICES["openai_agents"]

    def can_import(self, source: Path | str) -> bool:
        path = Path(source)
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json") and "framework" in content:
            try:
                data = yaml.safe_load(content)
                return isinstance(data, dict) and data.get("framework") in (
                    "openai_agents",
                    "openai",
                )
            except Exception:
                return False
        return "from agents" in content or "import Runner" in content

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        path = Path(source).resolve()
        if not path.is_file():
            raise AdapterError(f"OpenAI Agents source file not found: {path}")

        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json"):
            return self._import_from_fixture(content, path)

        return self._import_from_python_ast(content, path)

    def _import_from_fixture(self, content: str, path: Path) -> AgentIRManifest:
        data = yaml.safe_load(content)
        agents: list[AgentSpec] = []

        agent_items = data.get("agents") or [data]
        for item in agent_items:
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
                        id=t_data.get("id", t_data.get("name", "tool")),
                        name=t_data.get("name", "tool"),
                        description=t_data.get("description", ""),
                        input_schema=ToolInputSchema(properties=tuple(props)),
                    )
                )

            handoffs = [
                HandoffSpec(
                    target_agent_id=h.get("target"),
                    description=h.get("description", "Transfer to agent"),
                )
                for h in item.get("handoffs", [])
            ]

            guards = [
                GuardSpec(
                    name=g.get("name", "guard"),
                    stage=g.get("stage", "input"),
                    rule_type=g.get("rule_type", "regex_pattern"),
                    pattern_or_rule=g.get("pattern", ""),
                )
                for g in item.get("guardrails", [])
            ]

            agents.append(
                AgentSpec(
                    id=item.get("id", item.get("name", "agent")),
                    name=item.get("name", "Agent"),
                    model=ModelSpec(
                        provider="openai",
                        model_id=item.get("model", "gpt-4o"),
                    ),
                    instructions=InstructionsSpec(
                        system_prompt=item.get("instructions", "You are an OpenAI agent.")
                    ),
                    tools=tuple(tools),
                    handoffs=tuple(handoffs),
                    guards=tuple(guards),
                    provenance=SourceProvenance(
                        source_framework="openai_agents",
                        source_identifier=path.name,
                        source_file=str(path),
                    ),
                )
            )

        return AgentIRManifest(
            name=path.stem,
            agents=tuple(agents),
            provenance=SourceProvenance(
                source_framework="openai_agents",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

    def _import_from_python_ast(self, content: str, path: Path) -> AgentIRManifest:
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            raise AdapterError(f"Failed to parse OpenAI Agents Python AST: {e}") from e

        agent_name = "triage_agent"
        instructions = "You are a triage agent."
        model_id = "gpt-4o"

        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                func_name = ""
                if isinstance(call.func, ast.Name):
                    func_name = call.func.id
                if func_name == "Agent":
                    for kw in call.keywords:
                        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                            agent_name = str(kw.value.value)
                        elif kw.arg == "instructions" and isinstance(kw.value, ast.Constant):
                            instructions = str(kw.value.value)
                        elif kw.arg == "model" and isinstance(kw.value, ast.Constant):
                            model_id = str(kw.value.value)

        agent = AgentSpec(
            id=agent_name.lower().replace(" ", "_"),
            name=agent_name,
            model=ModelSpec(provider="openai", model_id=model_id),
            instructions=InstructionsSpec(system_prompt=instructions),
            provenance=SourceProvenance(
                source_framework="openai_agents",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=path.stem,
            agents=(agent,),
            provenance=SourceProvenance(
                source_framework="openai_agents",
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
            "# Target: OpenAI Agents SDK",
            "# Target version range: >=0.1.0,<1.0.0",
            "",
            "from agents import Agent, Runner",
            "",
        ]

        # Generate tools
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

        # Forward declare agents if handoffs exist
        agent_var_map: dict[str, str] = {}
        for a in manifest.agents:
            agent_var_map[a.id] = f"{a.id.lower().replace('-', '_')}_agent"

        for a in manifest.agents:
            handoff_refs = [
                agent_var_map[h.target_agent_id]
                for h in a.handoffs
                if h.target_agent_id in agent_var_map
            ]
            handoff_repr = f"[{', '.join(handoff_refs)}]" if handoff_refs else "[]"
            tools_repr = f"[{', '.join(tool_names)}]" if tool_names else "[]"

            code_lines.extend(
                [
                    f"{agent_var_map[a.id]} = Agent(",
                    f'    name="{a.name}",',
                    f'    model="{a.model.model_id}",',
                    f'    instructions="""{a.instructions.system_prompt}""",',
                    f"    tools={tools_repr},",
                    f"    handoffs={handoff_repr},",
                    ")",
                    "",
                ]
            )

        primary_agent = agent_var_map[manifest.agents[0].id] if manifest.agents else "agent"
        code_lines.extend(
            [
                'if __name__ == "__main__":',
                f'    result = Runner.run({primary_agent}, input="Hello from AgentIR")',
                "    print(result.final_output)",
            ]
        )

        agent_py = out_dir / "agent.py"
        agent_py.write_text("\n".join(code_lines) + "\n", encoding="utf-8")
        generated_files.append(agent_py)

        reqs = out_dir / "requirements.txt"
        reqs.write_text("openai-agents>=0.1.0\nopenai>=1.20.0\n", encoding="utf-8")
        generated_files.append(reqs)

        return generated_files
