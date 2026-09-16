"""LangGraph framework adapter for AgentIR."""

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
from agentir.domain.state import StateChannelSpec, StateSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.domain.workflow import WorkflowSpec


class LangGraphAdapter(FrameworkAdapter):
    """Adapter for importing from and exporting to LangGraph."""

    framework_name: str = "langgraph"
    framework_version_range: str = ">=0.2.0,<1.0.0"
    adapter_version: str = "0.1.0"

    def get_capabilities(self) -> dict[str, CapabilitySupport]:
        return FRAMEWORK_CAPABILITY_MATRICES["langgraph"]

    def can_import(self, source: Path | str) -> bool:
        path = Path(source)
        if not path.is_file():
            return False
        content = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml", ".json") and "framework" in content:
            try:
                data = yaml.safe_load(content)
                return isinstance(data, dict) and data.get("framework") == "langgraph"
            except Exception:
                return False
        return "StateGraph" in content or "langgraph" in content

    def import_manifest(self, source: Path | str) -> AgentIRManifest:
        path = Path(source).resolve()
        if not path.is_file():
            raise AdapterError(f"LangGraph source file not found: {path}")

        content = path.read_text(encoding="utf-8")

        # Check if structured fixture format
        if path.suffix in (".yaml", ".yml", ".json") and ("nodes" in content or "graph" in content):
            return self._import_from_fixture(content, path)

        return self._import_from_python_ast(content, path)

    def _import_from_fixture(self, content: str, path: Path) -> AgentIRManifest:
        """Import structured LangGraph declarative fixture."""
        data = yaml.safe_load(content)
        name = data.get("name", "langgraph_imported_graph")

        tools: list[ToolSpec] = []
        for t_data in data.get("tools", []):
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

        model_data = data.get("model", {})
        model = ModelSpec(
            provider=model_data.get("provider", "openai"),
            model_id=model_data.get("model_id", "gpt-4o"),
            temperature=model_data.get("temperature", 0.7),
        )

        agent = AgentSpec(
            id=data.get("agent_id", "langgraph_agent"),
            name=data.get("agent_name", "LangGraph Agent"),
            model=model,
            instructions=InstructionsSpec(
                system_prompt=data.get("system_prompt", "You are a helpful assistant.")
            ),
            tools=tuple(tools),
            provenance=SourceProvenance(
                source_framework="langgraph",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        channels: list[StateChannelSpec] = []
        for ch in data.get("state", {}).get("channels", []):
            channels.append(
                StateChannelSpec(
                    key=ch.get("key", "messages"),
                    type_name=ch.get("type", "list"),
                    reducer=ch.get("reducer", "append"),
                )
            )
        state_spec = StateSpec(schema_name="GraphState", channels=tuple(channels))

        nodes: list[NodeSpec] = []
        for n in data.get("nodes", []):
            nodes.append(
                NodeSpec(
                    id=n.get("id", "node"),
                    type=n.get("type", "agent"),
                    name=n.get("name", n.get("id", "node")),
                    agent_id=agent.id if n.get("type") == "agent" else None,
                    tool_id=n.get("tool_id"),
                )
            )

        edges: list[EdgeSpec] = []
        for e in data.get("edges", []):
            is_cond = e.get("is_conditional", False)
            edges.append(
                EdgeSpec(
                    source_node_id=e["source"],
                    target_node_id=e.get("target"),
                    is_conditional=is_cond,
                    path_map=e.get("path_map", {}),
                )
            )

        wf = WorkflowSpec(
            id=data.get("workflow_id", "langgraph_workflow"),
            name=name,
            entry_node_id=data.get("entry_node", nodes[0].id if nodes else "agent"),
            finish_node_ids=tuple(data.get("finish_nodes", ["END"])),
            nodes=tuple(nodes),
            edges=tuple(edges),
            state=state_spec,
            provenance=SourceProvenance(
                source_framework="langgraph",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=name,
            agents=(agent,),
            workflows=(wf,),
            provenance=SourceProvenance(
                source_framework="langgraph",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

    def _import_from_python_ast(self, content: str, path: Path) -> AgentIRManifest:
        """Statically inspect Python AST for LangGraph StateGraph definitions."""
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            raise AdapterError(f"Failed to parse Python AST for {path}: {e}") from e

        nodes: list[NodeSpec] = []
        edges: list[EdgeSpec] = []
        entry_node: str | None = None
        state_channels: list[StateChannelSpec] = []
        system_prompt: str = "You are a helpful assistant."
        model_id = "gpt-4o"
        provider = "openai"

        # Walk AST safely
        for stmt in tree.body:
            # Detect State TypedDict
            if isinstance(stmt, ast.ClassDef):
                for item in stmt.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        col_name = item.target.id
                        reducer = "append" if "messages" in col_name.lower() else "replace"
                        state_channels.append(
                            StateChannelSpec(key=col_name, type_name="Any", reducer=reducer)
                        )

            # Detect node and edge additions
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute):
                    method = call.func.attr
                    # builder.add_node("name", fn)
                    if method == "add_node" and len(call.args) >= 1:
                        if isinstance(call.args[0], ast.Constant) and isinstance(
                            call.args[0].value, str
                        ):
                            node_name = call.args[0].value
                            nodes.append(
                                NodeSpec(
                                    id=node_name,
                                    type="agent" if "tool" not in node_name else "tool",
                                    name=node_name,
                                )
                            )
                    # builder.add_edge("source", "target")
                    elif method == "add_edge" and len(call.args) >= 2:
                        src = (
                            call.args[0].value
                            if isinstance(call.args[0], ast.Constant)
                            else str(call.args[0])
                        )
                        dst = (
                            call.args[1].value
                            if isinstance(call.args[1], ast.Constant)
                            else str(call.args[1])
                        )
                        edges.append(EdgeSpec(source_node_id=str(src), target_node_id=str(dst)))
                    # builder.add_conditional_edges("source", router_fn, {...})
                    elif method == "add_conditional_edges" and len(call.args) >= 3:
                        src = (
                            call.args[0].value
                            if isinstance(call.args[0], ast.Constant)
                            else str(call.args[0])
                        )
                        path_map: dict[str, str] = {}
                        if isinstance(call.args[2], ast.Dict):
                            for k, v in zip(call.args[2].keys, call.args[2].values, strict=False):
                                if (
                                    isinstance(k, ast.Constant)
                                    and isinstance(v, ast.Constant)
                                    and isinstance(k.value, str)
                                    and isinstance(v.value, str)
                                ):
                                    path_map[k.value] = v.value
                        edges.append(
                            EdgeSpec(
                                source_node_id=str(src),
                                is_conditional=True,
                                path_map=path_map,
                            )
                        )
                    # builder.set_entry_point("node")
                    elif (
                        method == "set_entry_point"
                        and len(call.args) >= 1
                        and isinstance(call.args[0], ast.Constant)
                        and isinstance(call.args[0].value, str)
                    ):
                        entry_node = call.args[0].value

        if not nodes:
            nodes.append(NodeSpec(id="agent", type="agent", name="Primary Agent"))
        if not entry_node:
            entry_node = nodes[0].id

        agent = AgentSpec(
            id="langgraph_agent",
            name="LangGraph Agent",
            model=ModelSpec(provider=provider, model_id=model_id),
            instructions=InstructionsSpec(system_prompt=system_prompt),
            provenance=SourceProvenance(
                source_framework="langgraph",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        wf = WorkflowSpec(
            id=path.stem,
            name=f"LangGraph {path.stem}",
            entry_node_id=entry_node,
            finish_node_ids=("END",),
            nodes=tuple(nodes),
            edges=tuple(edges),
            state=StateSpec(
                schema_name="GraphState",
                channels=tuple(state_channels)
                if state_channels
                else (StateChannelSpec(key="messages", type_name="list", reducer="append"),),
            ),
            provenance=SourceProvenance(
                source_framework="langgraph",
                source_identifier=path.name,
                source_file=str(path),
            ),
        )

        return AgentIRManifest(
            name=path.stem,
            agents=(agent,),
            workflows=(wf,),
            provenance=SourceProvenance(
                source_framework="langgraph",
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
            "# Target: LangGraph (StateGraph compilation)",
            "# Target version range: >=0.2.0,<1.0.0",
            "",
            "from typing import Annotated, Literal, TypedDict",
            "from langgraph.graph import StateGraph, END",
            "from langgraph.graph.message import add_messages",
            "from langchain_core.messages import BaseMessage, HumanMessage, AIMessage",
            "from langchain_core.tools import tool",
            "",
        ]

        # Generate State
        code_lines.extend(
            [
                "class AgentState(TypedDict):",
                "    messages: Annotated[list[BaseMessage], add_messages]",
            ]
        )
        if manifest.workflows and manifest.workflows[0].state:
            for ch in manifest.workflows[0].state.channels:
                if ch.key != "messages":
                    code_lines.append(f"    {ch.key}: {ch.type_name}")
        code_lines.append("")

        # Generate Tools
        agent = manifest.agents[0] if manifest.agents else None
        tools = agent.tools if agent else ()
        if tools:
            for t in tools:
                code_lines.extend(
                    [
                        "@tool",
                        f"def {t.name.lower().replace(' ', '_')}() -> str:",
                        f'    """{t.description}"""',
                        f'    return "Executed {t.name}"',
                        "",
                    ]
                )

        # Generate Node handlers
        code_lines.extend(
            [
                "def agent_node(state: AgentState) -> dict:",
                '    """Main reasoning agent node."""',
                '    return {"messages": [AIMessage(content="Processed by AgentIR")]}',
                "",
                "def tool_node(state: AgentState) -> dict:",
                '    """Tool execution node."""',
                '    return {"messages": [AIMessage(content="Tool executed")]}',
                "",
            ]
        )

        # Build Graph
        wf = manifest.workflows[0] if manifest.workflows else None
        entry_node = wf.entry_node_id if wf else "agent_node"

        has_persistent_memory = False
        if manifest.agents and manifest.agents[0].memory:
            has_persistent_memory = manifest.agents[0].memory.persist_across_sessions

        code_lines.extend(
            [
                "builder = StateGraph(AgentState)",
                'builder.add_node("agent_node", agent_node)',
                'builder.add_node("tool_node", tool_node)',
                "",
                f'builder.set_entry_point("{entry_node}")',
            ]
        )

        if wf and wf.edges:
            for edge in wf.edges:
                if edge.is_conditional:
                    default_map = {"continue": "tool_node", "end": "END"}
                    path_map_repr = edge.path_map if edge.path_map else default_map
                    router_name = f"router_{edge.source_node_id}"
                    code_lines.extend(
                        [
                            f"def {router_name}(state: AgentState) -> str:",
                            '    return "continue"',
                            "",
                            (
                                f'builder.add_conditional_edges("{edge.source_node_id}", '
                                f"{router_name}, {path_map_repr})"
                            ),
                        ]
                    )
                else:
                    target = "END" if edge.target_node_id == "END" else f'"{edge.target_node_id}"'
                    code_lines.append(f'builder.add_edge("{edge.source_node_id}", {target})')
        else:
            code_lines.append('builder.add_edge("agent_node", "tool_node")')
            code_lines.append('builder.add_edge("tool_node", END)')

        if has_persistent_memory:
            code_lines.insert(6, "from langgraph.checkpoint.memory import MemorySaver")
            code_lines.extend(
                [
                    "",
                    "checkpointer = MemorySaver()",
                    "graph = builder.compile(checkpointer=checkpointer)",
                ]
            )
        else:
            code_lines.extend(
                [
                    "",
                    "graph = builder.compile()",
                ]
            )

        code_lines.extend(
            [
                "",
                'if __name__ == "__main__":',
                '    inputs = {"messages": [HumanMessage(content="Hello")]}',
                "    for event in graph.stream(inputs):",
                "        print(event)",
            ]
        )

        agent_py = out_dir / "agent.py"
        agent_py.write_text("\n".join(code_lines) + "\n", encoding="utf-8")
        generated_files.append(agent_py)

        # Generate requirements.txt
        reqs = out_dir / "requirements.txt"
        reqs.write_text(
            "langgraph>=0.2.0\nlangchain-core>=0.2.0\nlangchain-openai>=0.1.0\n",
            encoding="utf-8",
        )
        generated_files.append(reqs)

        return generated_files
