"""Rich presentation and formatting utilities for AgentIR CLI."""

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from agentir.analysis.diff import DiffCategory, SemanticDiffReport
from agentir.analysis.verification import VerificationReport
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.status import CompatibilityReport, SupportLevel
from agentir.capabilities.taxonomy import CAPABILITIES
from agentir.domain.manifest import AgentIRManifest
from agentir.schema.canonical import compute_canonical_hash

console = Console()
err_console = Console(stderr=True)


def output_json(data: Any) -> None:
    """Print structured data as indented JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_error(message: str, details: Any = None) -> None:
    err_console.print(f"[bold red]✗ Error:[/bold red] {message}")
    if details:
        err_console.print(Panel(str(details), title="Details", border_style="red"))


def render_inspect(manifest: AgentIRManifest) -> None:
    """Render a comprehensive inspect panel and tree."""
    canonical_hash = compute_canonical_hash(manifest)

    tree = Tree(f"[bold cyan]{manifest.name}[/bold cyan] (IR {manifest.ir_version})")
    tree.add(f"[dim]Canonical Hash:[/dim] [yellow]{canonical_hash}[/yellow]")

    if manifest.description:
        tree.add(f"[dim]Description:[/dim] {manifest.description}")

    # Agents Branch
    agents_branch = tree.add(f"[bold]Agents[/bold] ({len(manifest.agents)})")
    for a in manifest.agents:
        a_node = agents_branch.add(f"[green]{a.name}[/green] (`{a.id}`)")
        a_node.add(f"Model: [blue]{a.model.provider}/{a.model.model_id}[/blue]")
        if a.tools:
            tools_node = a_node.add(f"Tools ({len(a.tools)})")
            for t in a.tools:
                tools_node.add(f"[magenta]{t.name}[/magenta]: {t.description or 'No description'}")
        if a.handoffs:
            handoffs_node = a_node.add(f"Handoff Targets ({len(a.handoffs)})")
            for h in a.handoffs:
                handoffs_node.add(f"-> [cyan]{h.target_agent_id}[/cyan]: {h.description}")

    # Workflows Branch
    if manifest.workflows:
        wf_branch = tree.add(f"[bold]Workflows[/bold] ({len(manifest.workflows)})")
        for wf in manifest.workflows:
            w_node = wf_branch.add(f"[yellow]{wf.name}[/yellow] (`{wf.id}`)")
            w_node.add(f"Entry Node: `{wf.entry_node_id}`")
            w_node.add(f"Nodes: {len(wf.nodes)}, Edges: {len(wf.edges)}")

    console.print(Panel(tree, title="AgentIR Manifest Inspection", border_style="cyan"))


def render_compatibility(report: CompatibilityReport) -> None:
    """Render a compatibility report table."""
    status_style = "bold green" if report.is_compatible else "bold red"
    status_text = "COMPATIBLE" if report.is_compatible else "INCOMPATIBLE"

    console.print(
        f"\n[bold]Target Framework:[/bold] [cyan]{report.target_framework}[/cyan] | "
        f"Status: [{status_style}]{status_text}[/{status_style}] | "
        f"Score: [bold]{report.score:.1f}%[/bold]\n"
    )

    table = Table(title="Capability Breakdown", show_header=True)
    table.add_column("Capability", style="bold")
    table.add_column("Support Level")
    table.add_column("Risk")
    table.add_column("Notes")

    for n in report.native:
        table.add_row(
            n.capability_id, "[green]NATIVE[/green]", "[dim]none[/dim]", "Fully supported"
        )
    for a in report.adapter:
        table.add_row(
            a.capability_id,
            "[yellow]ADAPTER[/yellow]",
            f"[yellow]{a.semantic_loss_risk.value}[/yellow]",
            a.description or a.required_adapter_shim or "",
        )
    for e in report.emulated:
        table.add_row(
            e.capability_id,
            "[blue]EMULATED[/blue]",
            f"[bold yellow]{e.semantic_loss_risk.value}[/bold yellow]",
            e.emulation_strategy or "",
        )
    for u in report.unsupported:
        table.add_row(
            u.capability_id,
            "[bold red]UNSUPPORTED[/bold red]",
            f"[bold red]{u.semantic_loss_risk.value}[/bold red]",
            u.description or "",
        )

    console.print(table)

    if report.required_actions:
        console.print("\n[bold yellow]Required Actions / Recommendations:[/bold yellow]")
        for act in report.required_actions:
            console.print(f"  • {act}")


def render_diff(report: SemanticDiffReport) -> None:
    """Render semantic differences table."""
    if report.is_equivalent:
        console.print("[bold green]✓ Definitions are canonically equivalent.[/bold green]")
        return

    cat_colors = {
        DiffCategory.METADATA_ONLY: "dim",
        DiffCategory.ADDITIVE: "green",
        DiffCategory.BEHAVIORAL: "yellow",
        DiffCategory.BREAKING: "bold red",
    }
    color = cat_colors.get(report.overall_category, "white")
    impact_title = report.overall_category.value.upper()
    console.print(f"\n[bold]Semantic Difference Impact:[/bold] [{color}]{impact_title}[/{color}]\n")

    table = Table(title="Detected Differences", show_header=True)
    table.add_column("Path", style="cyan")
    table.add_column("Change")
    table.add_column("Category")
    table.add_column("Explanation")

    for e in report.entries:
        c_color = cat_colors.get(e.category, "white")
        table.add_row(
            e.path,
            e.change_type.upper(),
            f"[{c_color}]{e.category.value}[/{c_color}]",
            e.explanation,
        )

    console.print(table)


def render_verification(report: VerificationReport) -> None:
    """Render verification checks table."""
    status_style = "bold green" if report.is_valid else "bold red"
    status_text = "PASSED" if report.is_valid else "FAILED"

    console.print(
        f"\n[bold]Verification Status:[/bold] [{status_style}]{status_text}[/{status_style}] "
        f"(Errors: {len(report.errors)}, Warnings: {len(report.warnings)})\n"
    )

    table = Table(show_header=True)
    table.add_column("Rule Check", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    for c in report.checks:
        if c.passed:
            status = "[green]PASS[/green]"
        elif c.severity == "warning":
            status = "[yellow]WARN[/yellow]"
        else:
            status = "[bold red]FAIL[/bold red]"
        table.add_row(c.name, status, c.message)

    console.print(table)


def render_capabilities_list(framework: str | None = None) -> None:
    """Render capabilities table for taxonomy or a framework matrix."""
    if framework:
        fw_key = framework.lower().replace("-", "_")
        if fw_key not in FRAMEWORK_CAPABILITY_MATRICES:
            print_error(f"Unknown framework '{framework}'.")
            return
        matrix = FRAMEWORK_CAPABILITY_MATRICES[fw_key]
        table = Table(title=f"Declared Capabilities for {framework}", show_header=True)
        table.add_column("Capability", style="bold")
        table.add_column("Support Level")
        table.add_column("Semantic Risk")
        table.add_column("Details")

        for cap_id, supp in sorted(matrix.items()):
            if supp.support_level == SupportLevel.NATIVE:
                color = "green"
            elif supp.support_level in (SupportLevel.ADAPTER, SupportLevel.EMULATED):
                color = "yellow"
            else:
                color = "red"
            table.add_row(
                cap_id,
                f"[{color}]{supp.support_level.value.upper()}[/{color}]",
                supp.semantic_loss_risk.value,
                supp.description or supp.emulation_strategy or "",
            )
        console.print(table)
    else:
        table = Table(title="AgentIR Canonical Capability Taxonomy", show_header=True)
        table.add_column("Capability ID", style="bold cyan")
        table.add_column("Category")
        table.add_column("Name")
        table.add_column("Description")

        for cap_id, defn in sorted(CAPABILITIES.items()):
            table.add_row(cap_id, defn.category.value, defn.name, defn.description)
        console.print(table)
