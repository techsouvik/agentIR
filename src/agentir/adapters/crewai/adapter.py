"""CrewAI framework adapter for AgentIR."""

import ast
from pathlib import Path

import yaml

from agentir.adapters.base import FrameworkAdapter
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import CapabilitySupport
from agentir.domain.agent import AgentSpec
from agentir.domain.edge import EdgeSpec
from agentir.domain.exceptions import AdapterError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.node import NodeSpec
from agentir.domain.provenance import SourceProvenance
from agentir.domain.tool import ToolInputSchema, ToolSpec
from agentir.domain.workflow import WorkflowSpec


class CrewAIAdapter(FrameworkAdapter):
    """Adapter for importing from and exporting to CrewAI."""

    framework_name: str = "crewai"
    framework_version_range: str = ">=0.80.0,<1.0.0"
    adapter_version: str = "0.1.0"

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        return FRAMEWORK_CAPABILITY_MATRICES["crewai"]

    def can_import(self, source: Path | str) -> bool:
        path = Path(source)
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json") and "framework" in content:
            try:
                data = yaml.safe_load(content)
                return isinstance(data, dict) and data.get("framework") == "crewai"
            except Exception:
                return False
        return "from crewai" in content or "import Crew" in content or "Crew(" in content

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        path = Path(source).resolve()
        if not path.is_file():
            raise AdapterError(f"CrewAI source file not found: {path}")

        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json"):
            return self._import_from_fixture(content, path)

        return self._import_from_python_ast(content, path)

    def _import_from_fixture(self, content: str, path: Path) -> AgentIRManifest:
        data = yaml.safe_load(content)
        agents: list[AgentSpec] = []
        nodes: list[NodeSpec] = []
        edges: list[EdgeSpec] = []

        raw_agents = data.get("agents", [])
        for a_data in raw_agents:
            tools: list[ToolSpec] = []
            for t_data in a_data.get("tools", []):
                tools.append(
                    ToolSpec(
                        id=t_data.get("name", "tool"),
                        name=t_data.get("name", "tool"),
                        description=t_data.get("description", ""),
                        input_schema=ToolInputSchema(),
                    )
                )

            m_data = a_data.get("model", {})
            model = ModelSpec(
                provider=m_data.get("provider", "openai"),
                model_id=m_data.get("model_id", "gpt-4o"),
                temperature=m_data.get("temperature", 0.7),
            )

            role = a_data.get("role", "Worker")
            goal = a_data.get("goal", "")
            backstory = a_data.get("backstory", "")
            system_prompt = f"Role: {role}\nGoal: {goal}\nBackstory: {backstory}".strip()

            agent_id = a_data.get("id", role.lower().replace(" ", "_"))
            agents.append(
                AgentSpec(
                    id=agent_id,
                    name=a_data.get("name", role),
                    model=model,
                    instructions=InstructionsSpec(
                        system_prompt=system_prompt,
                        role=role,
                        persona=backstory,
                    ),
                    tools=tuple(tools),
                    provenance=SourceProvenance(
                        source_framework="crewai",
                        source_identifier=path.name,
                        source_file=str(path),
                    ),
                )
            )

        # Build workflow from tasks
        raw_tasks = data.get("tasks", [])
        prev_node_id: str | None = None
        for idx, t_data in enumerate(raw_tasks):
            node_id = f"task_{idx + 1}"
            assigned_agent = t_data.get("agent_id") or (agents[0].id if agents else None)
            nodes.append(
                NodeSpec(
                    id=node_id,
                    type="agent",
                    name=t_data.get("description", f"Task {idx + 1}")[:40],
                    agent_id=assigned_agent,
                )
            )
            if prev_node_id:
                edges.append(EdgeSpec(source_node_id=prev_node_id, target_node_id=node_id))
            prev_node_id = node_id

        if prev_node_id:
            edges.append(EdgeSpec(source_node_id=prev_node_id, target_node_id="END"))

        entry_node = nodes[0].id if nodes else "task_1"
        wf = WorkflowSpec(
            id=data.get("name", path.stem).lower().replace(" ", "_"),
            name=data.get("name", "Crew Process"),
            entry_node_id=entry_node,
            finish_node_ids=("END",),
            nodes=tuple(nodes),
            edges=tuple(edges),
            provenance=SourceProvenance(
                source_framework="crewai",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=data.get("name", path.stem),
            agents=tuple(agents),
            workflows=(wf,),
            provenance=SourceProvenance(
                source_framework="crewai",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

    def _import_from_python_ast(self, content: str, path: Path) -> AgentIRManifest:
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            raise AdapterError(f"Failed to parse CrewAI Python AST: {e}") from e

        agents: list[AgentSpec] = []
        for stmt in tree.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                func_name = ""
                if isinstance(call.func, ast.Name):
                    func_name = call.func.id
                if func_name == "Agent":
                    role = "Worker"
                    goal = "Complete task"
                    backstory = ""
                    for kw in call.keywords:
                        if kw.arg == "role" and isinstance(kw.value, ast.Constant):
                            role = str(kw.value.value)
                        elif kw.arg == "goal" and isinstance(kw.value, ast.Constant):
                            goal = str(kw.value.value)
                        elif kw.arg == "backstory" and isinstance(kw.value, ast.Constant):
                            backstory = str(kw.value.value)

                    prompt = f"Role: {role}\nGoal: {goal}\nBackstory: {backstory}"
                    agents.append(
                        AgentSpec(
                            id=role.lower().replace(" ", "_"),
                            name=role,
                            model=ModelSpec(provider="openai", model_id="gpt-4o"),
                            instructions=InstructionsSpec(
                                system_prompt=prompt,
                                role=role,
                                persona=backstory,
                            ),
                            provenance=SourceProvenance(
                                source_framework="crewai",
                                source_identifier=path.name,
                                source_file=str(path),
                            ),
                        )
                    )

        if not agents:
            agents.append(
                AgentSpec(
                    id="crew_agent",
                    name="Crew Worker",
                    model=ModelSpec(provider="openai", model_id="gpt-4o"),
                    instructions=InstructionsSpec(system_prompt="You are a CrewAI worker agent."),
                )
            )

        return AgentIRManifest(
            name=path.stem,
            agents=tuple(agents),
            provenance=SourceProvenance(
                source_framework="crewai",
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
            "# Auto-generated by AgentIR",
            "# Target: CrewAI",
            "# Target version range: >=0.80.0,<1.0.0",
            "",
            "from crewai import Agent, Task, Crew, Process",
            "",
        ]

        # Generate Agent variables
        agent_var_map: dict[str, str] = {}
        for _idx, a in enumerate(manifest.agents):
            var_name = f"agent_{a.id}" if len(manifest.agents) > 1 else "agent"
            agent_var_map[a.id] = var_name
            role = a.instructions.role or a.name
            goal = (
                a.instructions.guidelines[0]
                if a.instructions.guidelines
                else "Fulfill objectives"
            )
            raw_backstory = a.instructions.persona or a.instructions.system_prompt[:120]
            backstory = raw_backstory.replace('"', '\\"')

            code_lines.extend(
                [
                    f"{var_name} = Agent(",
                    f'    role="{role}",',
                    f'    goal="{goal}",',
                    f'    backstory="""{backstory}""",',
                    "    verbose=True,",
                    ")",
                    "",
                ]
            )

        # Generate Tasks
        task_vars: list[str] = []
        if manifest.workflows and manifest.workflows[0].nodes:
            first_var = list(agent_var_map.values())[0]
            for _idx, node in enumerate(manifest.workflows[0].nodes):
                task_var = f"task_{node.id}"
                task_vars.append(task_var)
                assigned_agent_var = agent_var_map.get(node.agent_id or "", first_var)
                code_lines.extend(
                    [
                        f"{task_var} = Task(",
                        f'    description="{node.name}",',
                        '    expected_output="Detailed findings and response.",',
                        f"    agent={assigned_agent_var},",
                        ")",
                        "",
                    ]
                )
        else:
            default_agent = list(agent_var_map.values())[0] if agent_var_map else "agent"
            code_lines.extend(
                [
                    "task_main = Task(",
                    '    description="Execute primary instructions.",',
                    '    expected_output="Complete response report.",',
                    f"    agent={default_agent},",
                    ")",
                    "",
                ]
            )
            task_vars.append("task_main")

        agents_repr = f"[{', '.join(agent_var_map.values())}]"
        tasks_repr = f"[{', '.join(task_vars)}]"

        has_memory = any(a.memory is not None for a in manifest.agents)
        mem_arg = "    memory=True,\n" if has_memory else ""

        code_lines.extend(
            [
                "crew = Crew(",
                f"    agents={agents_repr},",
                f"    tasks={tasks_repr},",
                f"{mem_arg}    process=Process.sequential,",
                ")",
                "",
                'if __name__ == "__main__":',
                "    result = crew.kickoff()",
                "    print(result)",
            ]
        )

        agent_py = out_dir / "agent.py"
        agent_py.write_text("\n".join(code_lines) + "\n", encoding="utf-8")
        generated_files.append(agent_py)

        reqs = out_dir / "requirements.txt"
        reqs.write_text("crewai>=0.80.0\n", encoding="utf-8")
        generated_files.append(reqs)

        return generated_files
