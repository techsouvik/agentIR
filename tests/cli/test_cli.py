"""Tests for the AgentIR CLI commands using CliRunner."""

import json
from pathlib import Path

from typer.testing import CliRunner

from agentir.cli.main import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_cli_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AgentIR v" in result.stdout

    json_res = runner.invoke(app, ["version", "--json"])
    assert json_res.exit_code == 0
    data = json.loads(json_res.stdout)
    assert data["version"] == "0.1.0"
    assert "langgraph" in data["registered_adapters"]


def test_cli_doctor() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "HEALTHY" in result.stdout

    json_res = runner.invoke(app, ["doctor", "--json"])
    assert json_res.exit_code == 0
    data = json.loads(json_res.stdout)
    assert data["status"] == "healthy"


def test_cli_capabilities() -> None:
    result = runner.invoke(app, ["capabilities"])
    assert result.exit_code == 0
    assert "model_calling" in result.stdout

    res_fw = runner.invoke(app, ["capabilities", "--framework", "langgraph"])
    assert res_fw.exit_code == 0
    assert "conditional_edges" in res_fw.stdout


def test_cli_init_and_validate(tmp_path: Path) -> None:
    out_file = tmp_path / "test_agent.yaml"
    init_res = runner.invoke(app, ["init", "support_bot", "-o", str(out_file), "-t", "tools"])
    assert init_res.exit_code == 0
    assert out_file.is_file()

    val_res = runner.invoke(app, ["validate", str(out_file)])
    assert val_res.exit_code == 0
    assert "valid" in val_res.stdout.lower()

    inspect_res = runner.invoke(app, ["inspect", str(out_file)])
    assert inspect_res.exit_code == 0
    assert "support_bot" in inspect_res.stdout


def test_cli_check(tmp_path: Path) -> None:
    manifest_file = tmp_path / "agent.yaml"
    runner.invoke(app, ["init", "checker_bot", "-o", str(manifest_file)])

    check_res = runner.invoke(app, ["check", str(manifest_file), "--target", "langgraph"])
    assert check_res.exit_code == 0
    assert "COMPATIBLE" in check_res.stdout


def test_cli_import_and_export(tmp_path: Path) -> None:
    src_fixture = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    imported_ir = tmp_path / "imported_agno.yaml"

    imp_res = runner.invoke(
        app,
        ["import", str(src_fixture), "--framework", "agno", "-o", str(imported_ir)],
    )
    assert imp_res.exit_code == 0
    assert imported_ir.is_file()

    export_dir = tmp_path / "exported_langgraph"
    exp_res = runner.invoke(
        app,
        ["export", str(imported_ir), "--target", "langgraph", "-o", str(export_dir)],
    )
    assert exp_res.exit_code == 0
    assert (export_dir / "agent.py").is_file()


def test_cli_diff(tmp_path: Path) -> None:
    file1 = tmp_path / "v1.yaml"
    file2 = tmp_path / "v2.yaml"
    runner.invoke(app, ["init", "v1", "-o", str(file1)])
    runner.invoke(app, ["init", "v2", "-o", str(file2)])

    diff_res = runner.invoke(app, ["diff", str(file1), str(file2)])
    assert diff_res.exit_code == 1  # non-zero for differences
    assert "BEHAVIORAL" in diff_res.stdout or "DIFFERENCE" in diff_res.stdout.upper()


def test_cli_verify(tmp_path: Path) -> None:
    manifest_file = tmp_path / "verify_agent.yaml"
    runner.invoke(app, ["init", "clean_agent", "-o", str(manifest_file)])

    ver_res = runner.invoke(app, ["verify", str(manifest_file)])
    assert ver_res.exit_code == 0
    assert "PASSED" in ver_res.stdout


def test_cli_migrate(tmp_path: Path) -> None:
    src_fixture = FIXTURES_DIR / "agno" / "sample_agent.yaml"
    out_dir = tmp_path / "migrated_langgraph"

    mig_res = runner.invoke(
        app,
        [
            "migrate",
            str(src_fixture),
            "--from",
            "agno",
            "--to",
            "langgraph",
            "-o",
            str(out_dir),
        ],
    )
    assert mig_res.exit_code == 0
    assert (out_dir / "agent.py").is_file()
    assert (out_dir / "MIGRATION_REPORT.md").is_file()
