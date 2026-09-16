"""AgentIR CLI — Command Line Interface for Agent Intermediate Representation."""

import platform
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from agentir.adapters.registry import (
    detect_framework,
    get_adapter,
    list_registered_adapters,
    resolve_framework_name,
)
from agentir.analysis.diff import compare_manifests
from agentir.analysis.verification import verify_manifest
from agentir.capabilities.analyzer import analyze_compatibility
from agentir.capabilities.matrix import FRAMEWORK_CAPABILITY_MATRICES
from agentir.capabilities.taxonomy import CAPABILITIES
from agentir.cli.discovery import find_manifest
from agentir.cli.presentation import (
    console,
    output_json,
    print_error,
    print_success,
    render_capabilities_list,
    render_compatibility,
    render_diff,
    render_inspect,
    render_verification,
)
from agentir.compiler.pipeline import compile_migration
from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AgentIRError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.domain.skill import SkillSpec
from agentir.domain.tool import ToolInputSchema, ToolParameterProperty, ToolSpec
from agentir.infrastructure.logging import setup_logging
from agentir.runtime.engine import DeterministicRuntime
from agentir.schema.canonical import compute_canonical_hash
from agentir.schema.serializer import (
    load_manifest_from_file,
    serialize_manifest_to_json,
    serialize_manifest_to_yaml,
)

app = typer.Typer(
    name="agentir",
    help="AgentIR — Framework-neutral intermediate representation and compiler for AI agents.",
    no_args_is_help=True,
)


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Verbose logs")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Quiet output")] = False,
) -> None:
    """AgentIR global options."""
    setup_logging(verbose=verbose, quiet=quiet)


@app.command()
def version(
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Show AgentIR version and system information."""
    data = {
        "version": "0.1.0",
        "ir_spec_version": "0.1.0",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "registered_adapters": list_registered_adapters(),
    }
    if json_output:
        output_json(data)
    else:
        typer.echo(f"AgentIR v{data['version']} (IR Spec v{data['ir_spec_version']})")
        typer.echo(f"Python {data['python_version']} on {data['platform']}")
        typer.echo(f"Adapters: {', '.join(data['registered_adapters'])}")


@app.command()
def init(
    name: Annotated[str | None, typer.Argument(help="Agent system name")] = None,
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    template: Annotated[str, typer.Option("-t", "--template")] = "minimal",
    interactive: Annotated[bool, typer.Option("--interactive/--no-interactive")] = True,
) -> None:
    """Scaffold a starter AgentIR manifest file with interactive assistance."""
    is_interactive = interactive and sys.stdin.isatty() and sys.stdout.isatty()
    target_name = name
    target_template = template

    if target_name is None:
        if is_interactive:
            console.print("[bold cyan]AgentIR Scaffolding Wizard[/bold cyan]")
            target_name = typer.prompt("Agent System Name", default="my_agent")
            target_template = typer.prompt(
                "Select Architecture Template",
                default="minimal",
            )
        else:
            target_name = "my_agent"

    target_output = output or Path("agentir.yaml")

    tool = ToolSpec(
        id="search_tool",
        name="Search Tool",
        description="Search documentation and web content",
        input_schema=ToolInputSchema(
            properties=(ToolParameterProperty(name="query", type="string", required=True),),
            required=("query",),
        ),
    )
    tools = (tool,) if target_template in ("tools", "multi-agent", "skills") else ()

    skills: tuple[SkillSpec, ...] = ()
    if target_template == "skills":
        skills = (
            SkillSpec(
                id="research_skill",
                name="Research Skill",
                description="Web research methodology",
                instructions="Always cross-reference multiple primary sources.",
                tools=(tool,),
            ),
        )

    agent = AgentSpec(
        id=f"{target_name}_agent",
        name=target_name.replace("_", " ").title(),
        model=ModelSpec(provider="openai", model_id="gpt-4o", temperature=0.7),
        instructions=InstructionsSpec(
            system_prompt=f"You are {target_name}, a helpful autonomous AI agent.",
            guidelines=("Be concise", "Ensure accuracy"),
        ),
        tools=tools,
        skills=skills,
    )
    manifest = AgentIRManifest(name=target_name, agents=(agent,))

    content = serialize_manifest_to_yaml(manifest)
    target_output.write_text(content, encoding="utf-8")
    print_success(f"Initialized AgentIR manifest at '{target_output}'.")


@app.command()
def validate(
    path: Annotated[Path | None, typer.Argument(help="Manifest path (auto-discovered)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Validate syntax, schema, and domain invariants of an AgentIR manifest."""
    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
        manifest.validate_invariants()
        canonical_hash = compute_canonical_hash(manifest)

        if json_output:
            output_json({
                "valid": True,
                "file": str(manifest_path),
                "name": manifest.name,
                "canonical_hash": canonical_hash,
                "agents_count": len(manifest.agents),
                "workflows_count": len(manifest.workflows),
            })
        else:
            short_h = canonical_hash[:12]
            print_success(f"Manifest '{manifest_path.name}' is valid! [dim]({short_h}...)[/dim]")
    except Exception as e:
        if json_output:
            output_json({"valid": False, "file": str(path) if path else None, "error": str(e)})
        else:
            print_error("Validation failed", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def inspect(
    path: Annotated[Path | None, typer.Argument(help="Manifest path (auto-discovered)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Inspect and display the structure of an AgentIR manifest."""
    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
        if json_output:
            data = {
                "name": manifest.name,
                "file": str(manifest_path),
                "ir_version": manifest.ir_version,
                "canonical_hash": compute_canonical_hash(manifest),
                "agents": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "model": f"{a.model.provider}/{a.model.model_id}",
                        "tools": [t.id for t in a.tools],
                        "skills": [s.id for s in a.skills],
                        "handoffs": [h.target_agent_id for h in a.handoffs],
                    }
                    for a in manifest.agents
                ],
                "workflows": [
                    {
                        "id": w.id,
                        "entry_node": w.entry_node_id,
                        "node_count": len(w.nodes),
                        "edge_count": len(w.edges),
                    }
                    for w in manifest.workflows
                ],
            }
            output_json(data)
        else:
            render_inspect(manifest)
    except Exception as e:
        print_error("Failed to inspect manifest", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def capabilities(
    framework: Annotated[str | None, typer.Option("-f", "--framework", help="Framework")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Display the AgentIR capability taxonomy or framework support matrices."""
    if json_output:
        if framework:
            fw_key, suggestions = resolve_framework_name(framework)
            if not fw_key or fw_key not in FRAMEWORK_CAPABILITY_MATRICES:
                suggest_msg = f" Did you mean '{suggestions[0]}'?" if suggestions else ""
                print_error(f"Unknown framework '{framework}'.{suggest_msg}")
                raise typer.Exit(code=1)
            matrix = FRAMEWORK_CAPABILITY_MATRICES[fw_key]
            output_json({
                "framework": fw_key,
                "capabilities": {
                    k: {
                        "level": v.support_level.value,
                        "risk": v.semantic_loss_risk.value,
                        "description": v.description,
                    }
                    for k, v in matrix.items()
                },
            })
        else:
            output_json({
                "taxonomy": {
                    k: {
                        "name": v.name,
                        "category": v.category.value,
                        "description": v.description,
                    }
                    for k, v in CAPABILITIES.items()
                }
            })
    else:
        render_capabilities_list(framework)


@app.command()
def check(
    path: Annotated[Path | None, typer.Argument(help="Manifest path")] = None,
    target: Annotated[str, typer.Option("-t", "--target", help="Target framework")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Analyze compatibility of an AgentIR manifest against a target framework."""
    if not target:
        print_error("Missing required option '--target' / '-t' (e.g. --target langgraph)")
        raise typer.Exit(code=1)

    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)

        resolved_target, suggestions = resolve_framework_name(target)
        if not resolved_target:
            suggest_str = f" Did you mean '{suggestions[0]}'?" if suggestions else ""
            print_error(f"Unknown target framework '{target}'.{suggest_str}")
            raise typer.Exit(code=1)

        report = analyze_compatibility(manifest, resolved_target)

        if json_output:
            output_json(report.to_dict())
        else:
            render_compatibility(report)

        if not report.is_compatible:
            raise typer.Exit(code=2)
    except AgentIRError as e:
        print_error("Compatibility check failed", str(e))
        raise typer.Exit(code=1) from e


@app.command(name="import")
def import_cmd(
    source: Annotated[Path, typer.Argument(help="Source file or directory")],
    framework: Annotated[str, typer.Option("-f", "--framework", help="Source framework")] = "",
    output: Annotated[Path | None, typer.Option("-o", "--output", help="Output path")] = None,
    format_type: Annotated[str, typer.Option("--format", help="yaml|json")] = "yaml",
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Import a framework agent or workflow definition into canonical AgentIR."""
    resolved_framework = framework
    if not resolved_framework:
        detected = detect_framework(source)
        if detected:
            resolved_framework = detected
            if not json_output:
                msg = f"[dim]Auto-detected framework: [bold cyan]{detected}[/bold cyan][/dim]"
                console.print(msg)
        else:
            available = list_registered_adapters()
            print_error(
                f"Could not auto-detect framework for '{source}'. "
                f"Please specify --framework. Available: {available}"
            )
            raise typer.Exit(code=1)

    try:
        adapter = get_adapter(resolved_framework)
        manifest = adapter.import_manifest(source)

        if output:
            is_json = format_type == "json"
            content = (
                serialize_manifest_to_json(manifest)
                if is_json
                else serialize_manifest_to_yaml(manifest)
            )
            output.write_text(content, encoding="utf-8")
            if json_output:
                output_json(
                    {"success": True, "output_file": str(output), "manifest": manifest.name}
                )
            else:
                print_success(f"Imported from '{source}' to '{output}'.")
        else:
            if json_output or format_type == "json":
                print(serialize_manifest_to_json(manifest))
            else:
                print(serialize_manifest_to_yaml(manifest))
    except Exception as e:
        print_error(f"Import failed for '{source}'", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def export(
    path: Annotated[Path | None, typer.Argument(help="Manifest path")] = None,
    target: Annotated[str, typer.Option("-t", "--target", help="Target framework")] = "",
    output: Annotated[Path, typer.Option("-o", "--output", help="Output directory")] = Path("dist"),
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Export an AgentIR manifest into target framework code and configurations."""
    if not target:
        print_error("Missing required option '--target' / '-t'")
        raise typer.Exit(code=1)

    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
        adapter = get_adapter(target)
        generated = adapter.export_manifest(manifest, output)

        if json_output:
            output_json({
                "success": True,
                "target": target,
                "output_directory": str(output),
                "generated_files": [str(p) for p in generated],
            })
        else:
            print_success(f"Exported {len(generated)} file(s) for '{target}' to '{output}':")
            for f in generated:
                typer.echo(f"  • {f.name}")
    except Exception as e:
        print_error(f"Export failed for target '{target}'", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def migrate(
    source: Annotated[Path, typer.Argument(help="Source artifact to migrate")],
    from_framework: Annotated[str, typer.Option("--from", help="Source framework")] = "",
    to_framework: Annotated[str, typer.Option("--to", help="Target framework")] = "",
    output: Annotated[Path, typer.Option("-o", "--output")] = Path("migrated_project"),
    force: Annotated[bool, typer.Option("--force", help="Force migration")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Execute end-to-end migration between two agent frameworks."""
    if not to_framework:
        print_error("Missing required option '--to'")
        raise typer.Exit(code=1)

    resolved_from = from_framework
    if not resolved_from:
        detected = detect_framework(source)
        if detected:
            resolved_from = detected
            if not json_output:
                msg = f"[dim]Auto-detected framework: [bold cyan]{detected}[/bold cyan][/dim]"
                console.print(msg)
        else:
            print_error("Could not auto-detect source framework. Please specify '--from'.")
            raise typer.Exit(code=1)

    try:
        if resolved_from.lower() == "agentir":
            manifest = load_manifest_from_file(source)
        else:
            src_adapter = get_adapter(resolved_from)
            manifest = src_adapter.import_manifest(source)

        result = compile_migration(
            manifest=manifest,
            target_framework=to_framework,
            output_directory=output,
            force=force,
            generate_report=True,
        )

        if json_output:
            output_json(result.to_dict())
        else:
            msg = (
                f"Migration completed! Migrated '{source.name}' from "
                f"{resolved_from} to {to_framework}."
            )
            print_success(msg)
            typer.echo(f"Output directory: {result.output_directory}")
            typer.echo(f"Compatibility score: {result.plan.compatibility.score:.1f}%")
            if result.report_path:
                typer.echo(f"Audit report: {result.report_path}")
            if result.plan.warnings:
                typer.echo("\nWarnings:")
                for w in result.plan.warnings:
                    typer.echo(f"  • {w}")
    except Exception as e:
        print_error("Migration failed", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def diff(
    path_a: Annotated[Path, typer.Argument(help="First manifest path")],
    path_b: Annotated[Path, typer.Argument(help="Second manifest path")],
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Semantically diff two AgentIR definitions."""
    try:
        m1 = load_manifest_from_file(path_a)
        m2 = load_manifest_from_file(path_b)
        report = compare_manifests(m1, m2)

        if json_output:
            output_json(report.to_dict())
        else:
            render_diff(report)

        if not report.is_equivalent:
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error("Diff failed", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def verify(
    path: Annotated[Path | None, typer.Argument(help="Manifest path")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Run full verification suite on an AgentIR manifest."""
    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
        report = verify_manifest(manifest)

        if json_output:
            output_json(report.to_dict())
        else:
            render_verification(report)

        if not report.is_valid:
            raise typer.Exit(code=1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error("Verification encountered an error", str(e))
        raise typer.Exit(code=1) from e


@app.command()
def run(
    path: Annotated[Path | None, typer.Argument(help="Manifest path")] = None,
    input_text: Annotated[str | None, typer.Option("-i", "--input", help="User input")] = None,
    max_turns: Annotated[int, typer.Option("--max-turns", help="Maximum turns")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Run a deterministic dry-run simulation or interactive conversational REPL."""
    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
    except Exception as e:
        print_error("Could not load manifest", str(e))
        raise typer.Exit(code=1) from e

    runtime = DeterministicRuntime()

    # One-shot mode
    if input_text is not None or json_output or not sys.stdin.isatty():
        prompt = input_text or "Hello"
        result = runtime.run(manifest, user_input=prompt, max_turns=max_turns)
        if json_output:
            output_json(result.to_dict())
        else:
            status_style = "bold green" if result.success else "bold red"
            status_str = "SUCCESS" if result.success else "HALTED"
            msg = f"Simulation completed! Status: [{status_style}]{status_str}[/{status_style}]"
            print_success(msg)
            typer.echo(f"Final output: {result.final_output}")
            typer.echo(f"Total steps: {len(result.steps)}")
            if result.halt_reason:
                typer.echo(f"Halt reason: {result.halt_reason}")
        return

    # Interactive REPL mode
    primary = manifest.agents[0] if manifest.agents else None
    agent_title = f"{primary.name} ({primary.model.model_id})" if primary else manifest.name
    console.print(
        f"\n[bold cyan]AgentIR Interactive Simulation REPL[/bold cyan] "
        f"[dim]• Agent: [green]{agent_title}[/green] • Type 'exit' to quit[/dim]\n"
    )

    while True:
        try:
            user_msg = console.input("[bold blue]User > [/bold blue]").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ("exit", "quit", "q"):
                console.print("[dim]Exiting simulation REPL.[/dim]")
                break

            res = runtime.run(manifest, user_input=user_msg, max_turns=max_turns)
            if res.success:
                console.print(f"[bold green]Agent >[/bold green] {res.final_output}")
                tool_calls = [s for s in res.steps if s.action == "tool_call"]
                if tool_calls:
                    for tc in tool_calls:
                        msg = f"  [dim]↳ Tool: {tc.input_payload} -> {tc.output_payload}[/dim]"
                        console.print(msg)
            else:
                console.print(f"[bold red]Halted >[/bold red] {res.final_output}")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Simulation REPL terminated.[/dim]")
            break


@app.command()
def doctor(
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Diagnose AgentIR installation, dependencies, and environment health."""
    diag: dict[str, Any] = {
        "status": "healthy",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "registered_adapters": list_registered_adapters(),
        "dependencies": {},
        "write_permission": False,
    }

    for dep in ("pydantic", "rich", "structlog", "yaml", "orjson", "httpx"):
        try:
            __import__(dep)
            diag["dependencies"][dep] = "installed"
        except ImportError:
            diag["dependencies"][dep] = "missing"
            diag["status"] = "degraded"

    try:
        test_file = Path(".agentir_doctor_test")
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        diag["write_permission"] = True
    except Exception:
        diag["write_permission"] = False
        diag["status"] = "degraded"

    if json_output:
        output_json(diag)
    else:
        status_style = "bold green" if diag["status"] == "healthy" else "bold red"
        typer.echo(f"AgentIR Doctor: [{status_style}]{diag['status'].upper()}[/{status_style}]")
        typer.echo(f"Python: {diag['python']} ({diag['platform']})")
        typer.echo(f"Registered Adapters: {', '.join(diag['registered_adapters'])}")
        typer.echo(f"Write permissions: {'OK' if diag['write_permission'] else 'FAILED'}")


mcp_app = typer.Typer(name="mcp", help="Model Context Protocol (MCP) commands.")
app.add_typer(mcp_app)


@mcp_app.command(name="export")
def mcp_export(
    path: Annotated[Path | None, typer.Argument(help="Manifest path")] = None,
    output: Annotated[Path, typer.Option("-o", "--output")] = Path("mcp_server"),
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Export AgentIR tools as an executable MCP tool server."""
    try:
        manifest_path = find_manifest(path)
        manifest = load_manifest_from_file(manifest_path)
        adapter = get_adapter("mcp")
        files = adapter.export_manifest(manifest, output)
        if json_output:
            output_json({"success": True, "files": [str(f) for f in files]})
        else:
            print_success(f"Exported MCP tool server to '{output}'.")
    except Exception as e:
        print_error("MCP export failed", str(e))
        raise typer.Exit(code=1) from e


@mcp_app.command(name="import")
def mcp_import(
    source: Annotated[Path, typer.Argument(help="Path to MCP tools JSON catalog")],
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="JSON output")] = False,
) -> None:
    """Import tools from an MCP catalog into AgentIR."""
    try:
        adapter = get_adapter("mcp")
        manifest = adapter.import_manifest(source)
        if output:
            content = serialize_manifest_to_yaml(manifest)
            output.write_text(content, encoding="utf-8")
            if json_output:
                output_json({"success": True, "output": str(output)})
            else:
                print_success(f"Imported MCP catalog to '{output}'.")
        else:
            if json_output:
                output_json(serialize_manifest_to_json(manifest))
            else:
                print(serialize_manifest_to_yaml(manifest))
    except Exception as e:
        print_error("MCP import failed", str(e))
        raise typer.Exit(code=1) from e


# Aliases for effortless developer experience
app.command(name="sim", help="Alias for 'run'")(run)
app.command(name="doc", help="Alias for 'doctor'")(doctor)
app.command(name="cap", help="Alias for 'capabilities'")(capabilities)
app.command(name="show", help="Alias for 'inspect'")(inspect)


if __name__ == "__main__":
    app()
