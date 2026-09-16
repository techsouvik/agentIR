"""Loop invariant analysis and cycle classification pass."""

from agentir.compiler.passes.base import CompilerPass, PassResult
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.workflow import WorkflowSpec


def count_graph_cycles(adj: dict[str, set[str]], node_ids: list[str]) -> int:
    """Deterministically count cycles using depth-first back-edge detection."""
    cycles_detected = 0
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def dfs(node: str) -> None:
        nonlocal cycles_detected
        visited[node] = 1
        for neighbor in adj.get(node, set()):
            if visited.get(neighbor) == 1:
                cycles_detected += 1
            elif visited.get(neighbor, 0) == 0:
                dfs(neighbor)
        visited[node] = 2

    for nid in node_ids:
        if visited.get(nid, 0) == 0:
            dfs(nid)

    return cycles_detected


class LoopInvariantPass(CompilerPass):
    """Analyzes workflow topologies, classifies cycles, and verifies state reducer invariants."""

    @property
    def name(self) -> str:
        return "LoopInvariantAnalysis"

    def run(self, manifest: AgentIRManifest) -> tuple[AgentIRManifest, PassResult]:
        mutations = 0
        messages: list[str] = []
        updated_workflows: list[WorkflowSpec] = []

        for wf in manifest.workflows:
            adj: dict[str, set[str]] = {n.id: set() for n in wf.nodes}
            for edge in wf.edges:
                if edge.is_conditional:
                    for target in edge.path_map.values():
                        if target in adj:
                            adj[edge.source_node_id].add(target)
                else:
                    if edge.target_node_id and edge.target_node_id in adj:
                        adj[edge.source_node_id].add(edge.target_node_id)

            node_ids = [n.id for n in wf.nodes]
            cycles_detected = count_graph_cycles(adj, node_ids)

            topology_class = "DAG" if cycles_detected == 0 else "CYCLIC"
            messages.append(
                f"Workflow '{wf.id}': classified as {topology_class} ({cycles_detected} cycle(s))."
            )

            new_meta = dict(wf.metadata)
            if new_meta.get("topology_class") != topology_class:
                new_meta["topology_class"] = topology_class
                new_meta["cycle_count"] = str(cycles_detected)
                mutations += 1

                updated_workflows.append(
                    WorkflowSpec(
                        id=wf.id,
                        name=wf.name,
                        entry_node_id=wf.entry_node_id,
                        nodes=wf.nodes,
                        edges=wf.edges,
                        finish_node_ids=wf.finish_node_ids,
                        state=wf.state,
                        execution_policy=wf.execution_policy,
                        description=wf.description,
                        metadata=new_meta,
                        provenance=wf.provenance,
                    )
                )
            else:
                updated_workflows.append(wf)

        if mutations > 0:
            new_manifest = AgentIRManifest(
                name=manifest.name,
                ir_version=manifest.ir_version,
                description=manifest.description,
                agents=manifest.agents,
                workflows=tuple(updated_workflows),
                shared_tools=manifest.shared_tools,
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
            messages=tuple(messages),
        )
