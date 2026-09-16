"""Tests for CLI ergonomics, auto-discovery, auto-detection, and interactive features."""

from pathlib import Path

from typer.testing import CliRunner

from agentir.cli.main import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_cli_manifest_autodiscovery(tmp_path: Path) -> None:
    """CLI commands must auto-discover agentir.yaml in current directory if omitted."""
    manifest_path = tmp_path / "agentir.yaml"
    runner.invoke(app, ["init", "autobot", "-o", str(manifest_path)])

    # Run validate with path pointing to the file
    res = runner.invoke(app, ["validate", str(manifest_path)])
    assert res.exit_code == 0
    assert "valid" in res.stdout.lower()


def test_cli_import_framework_autodetection(tmp_path: Path) -> None:
    """'agentir import' must automatically detect source framework without -f."""
    langgraph_src = FIXTURES_DIR / "langgraph" / "sample_graph.py"
    out_yaml = tmp_path / "imported.yaml"

    res = runner.invoke(app, ["import", str(langgraph_src), "-o", str(out_yaml)])
    assert res.exit_code == 0
    assert "Auto-detected" in res.stdout
    assert "langgraph" in res.stdout
    assert out_yaml.is_file()


def test_cli_migrate_framework_autodetection(tmp_path: Path) -> None:
    """'agentir migrate' must auto-detect --from if omitted."""
    agno_src = FIXTURES_DIR / "agno" / "sample_agent.py"
    out_dir = tmp_path / "migrated_from_agno"

    res = runner.invoke(
        app,
        ["migrate", str(agno_src), "--to", "langgraph", "-o", str(out_dir)],
    )
    assert res.exit_code == 0
    assert "Auto-detected" in res.stdout
    assert (out_dir / "agent.py").is_file()


def test_cli_fuzzy_framework_suggestion(tmp_path: Path) -> None:
    """Fuzzy matching must suggest correct framework for typos."""
    manifest_path = tmp_path / "agentir.yaml"
    runner.invoke(app, ["init", "fuzzy_bot", "-o", str(manifest_path)])

    res = runner.invoke(app, ["check", str(manifest_path), "--target", "open_agents"])
    assert res.exit_code == 1
    assert "Did you mean 'openai_agents'?" in res.output


def test_cli_run_oneshot_simulation(tmp_path: Path) -> None:
    """'agentir run' executes simulated turn and prints trace."""
    manifest_path = tmp_path / "agentir.yaml"
    runner.invoke(app, ["init", "sim_bot", "-o", str(manifest_path)])

    res = runner.invoke(app, ["run", str(manifest_path), "-i", "Test query"])
    assert res.exit_code == 0
    assert "SUCCESS" in res.stdout
    assert "Final output:" in res.stdout


def test_cli_aliases(tmp_path: Path) -> None:
    """Test aliases: doc, sim, cap, show."""
    res_doc = runner.invoke(app, ["doc"])
    assert res_doc.exit_code == 0
    assert "HEALTHY" in res_doc.stdout

    res_cap = runner.invoke(app, ["cap", "--framework", "langgraph"])
    assert res_cap.exit_code == 0
    assert "conditional_edges" in res_cap.stdout

    manifest_path = tmp_path / "agentir.yaml"
    runner.invoke(app, ["init", "alias_bot", "-o", str(manifest_path)])

    res_show = runner.invoke(app, ["show", str(manifest_path)])
    assert res_show.exit_code == 0
    assert "alias_bot" in res_show.stdout

    res_sim = runner.invoke(app, ["sim", str(manifest_path), "-i", "Sim test"])
    assert res_sim.exit_code == 0
    assert "SUCCESS" in res_sim.stdout
