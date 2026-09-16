"""Dead node and unreachable edge elimination compiler pass."""

from collections import deque

from agentir.compiler.passes.base import CompilerPass, PassResult
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.workflow import WorkflowSpec


class DeadNodeEliminationPass(CompilerPass):
    """Prunes unreachable nodes and dead edges from all workflow graphs."""

    @property
    def name(self) -> str:
        return "DeadNodeElimination"

    def run(self, manifest: AgentIRManifest) -> tuple[AgentIRManifest, PassResult]:
        mutations = 0
        messages: list[str] = []
        optimized_workflows: list[WorkflowSpec] = []

        for wf in manifest.workflows:
            # 1. Build adjacency list
            adj: dict[str, set[str]] = {n.id: set() for n in wf.nodes}
            adj["END"] = set()

            for edge in wf.edges:
                if edge.is_conditional:
                    for target in edge.path_map.values():
                        if edge.source_node_id in adj:
                            adj[edge.source_node_id].add(target)
                else:
                    if edge.target_node_id and edge.source_node_id in adj:
                        adj[edge.source_node_id].add(edge.target_node_id)

            # 2. Forward BFS reachability from entry node
            reachable: set[str] = set()
            queue = deque([wf.entry_node_id])
            while queue:
                curr = queue.popleft()
                if curr not in reachable:
                    reachable.add(curr)
                    for neighbor in adj.get(curr, set()):
                        if neighbor not in reachable and neighbor in adj:
                            queue.append(neighbor)

            # 3. Prune dead nodes
            initial_node_count = len(wf.nodes)
            surviving_nodes = tuple(n for n in wf.nodes if n.id in reachable)
            pruned_node_count = initial_node_count - len(surviving_nodes)

            # 4. Prune dead edges
            surviving_edges = tuple(
                e for e in wf.edges
                if e.source_node_id in reachable and (
                    e.is_conditional or (e.target_node_id in reachable or e.target_node_id == "END")
                )
            )
            pruned_edge_count = len(wf.edges) - len(surviving_edges)

            total_wf_mutations = pruned_node_count + pruned_edge_count
            if total_wf_mutations > 0:
                mutations += total_wf_mutations
                msg = (
                    f"Workflow '{wf.id}': pruned {pruned_node_count} unreachable node(s) and "
                    f"{pruned_edge_count} dead edge(s)."
                )
                messages.append(msg)
                optimized_workflows.append(
                    WorkflowSpec(
                        id=wf.id,
                        name=wf.name,
                        entry_node_id=wf.entry_node_id,
                        nodes=surviving_nodes,
                        edges=surviving_edges,
                        finish_node_ids=wf.finish_node_ids,
                        state=wf.state,
                        execution_policy=wf.execution_policy,
                        description=wf.description,
                        metadata=wf.metadata,
                        provenance=wf.provenance,
                    )
                )
            else:
                optimized_workflows.append(wf)

        if mutations > 0:
            new_manifest = AgentIRManifest(
                name=manifest.name,
                ir_version=manifest.ir_version,
                description=manifest.description,
                agents=manifest.agents,
                workflows=tuple(optimized_workflows),
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
            messages=("All workflow nodes and edges are reachable; 0 dead code.",),
        )
