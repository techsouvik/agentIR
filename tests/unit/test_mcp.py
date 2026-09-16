"""Unit tests for Model Context Protocol (MCP) adapter."""

import json
import tempfile
from pathlib import Path

from agentir.adapters.registry import get_adapter


def test_mcp_import_and_export() -> None:
    adapter = get_adapter("mcp")
    assert adapter.framework_name == "mcp"

    sample_catalog = {
        "server_name": "filesystem_server",
        "tools": [
            {
                "name": "read_file",
                "description": "Read file contents from disk",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute path to file"}
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "list_directory",
                "description": "List files in directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dir": {"type": "string", "description": "Directory path"}
                    },
                    "required": ["dir"],
                },
            },
        ],
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        cat_file = Path(tmp_dir) / "catalog.json"
        cat_file.write_text(json.dumps(sample_catalog), encoding="utf-8")

        assert adapter.can_import(cat_file)
        manifest = adapter.import_manifest(cat_file)

        assert manifest.name == "filesystem_server"
        assert len(manifest.shared_tools) == 2
        tool_names = {t.name for t in manifest.shared_tools}
        assert tool_names == {"read_file", "list_directory"}

        out_dir = Path(tmp_dir) / "exported_mcp"
        files = adapter.export_manifest(manifest, out_dir)
        file_names = {f.name for f in files}
        assert "mcp_server.py" in file_names
        assert "claude_desktop_config.json" in file_names

        server_code = (out_dir / "mcp_server.py").read_text(encoding="utf-8")
        assert "read_file" in server_code
        assert "list_directory" in server_code
