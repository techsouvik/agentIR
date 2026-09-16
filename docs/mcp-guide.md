# Model Context Protocol (MCP) Integration Guide

The **Model Context Protocol (MCP)** is an open standard developed to standardize how applications supply tools, data resources, and prompt context to AI models.

AgentIR provides bidirectional interoperability with MCP:
1. **Import MCP Catalogs**: Convert external MCP tool catalogs directly into canonical `ToolSpec` definitions.
2. **Export MCP Servers**: Compile AgentIR tools into standalone, runnable MCP tool servers (`mcp_server.py`) and Claude Desktop configuration snippets.

---

## 1. Ingesting Tools from MCP

If you have an existing MCP server or catalog JSON (e.g. `mcp_catalog.json`):

```json
{
  "server_name": "filesystem_server",
  "tools": [
    {
      "name": "read_file",
      "description": "Read file contents from disk",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": { "type": "string", "description": "Absolute path to file" }
        },
        "required": ["path"]
      }
    }
  ]
}
```

Import it into AgentIR:

```bash
agentir mcp import mcp_catalog.json -o filesystem_agent.yaml
```

The tool is converted to a canonical `ToolSpec` with JSON Schema typing and attached to an AgentIR manifest.

---

## 2. Exporting an MCP Tool Server

Any AgentIR manifest containing tools can be compiled into an MCP tool server:

```bash
agentir mcp export my_agent.yaml -o ./mcp_export
```

This generates:
- `mcp_server.py`: A Python MCP server exposing `tools/list` and `tools/call`.
- `claude_desktop_config.json`: Ready to copy into Claude Desktop's `claude_desktop_config.json`.

---

## 3. Configuring Claude Desktop

Copy the generated configuration snippet into your Claude Desktop configuration:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my_agent_tools": {
      "command": "python",
      "args": ["/path/to/mcp_export/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop, and your AgentIR tools will be immediately accessible in Claude!
