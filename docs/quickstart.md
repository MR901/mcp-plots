# Quickstart Guide

Get MCP Plots running in your environment in under 5 minutes.

## Prerequisites

- MCP-compatible client (Cursor, Continue, etc.)
- Python 3.10+ with pip

## Installation

```bash
pip install mcp-plots
```

Verify installation:
```bash
mcp-plots --version
```

## MCP Client Configuration (Choose a route)

### Cursor IDE

1. **Locate config file**: `~/.cursor/mcp.json` (create if missing)

2. **Route A — PyPI** (simple):
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": ["--transport", "stdio"]
    }
  }
}
```

3. **Route B — uvx (zero-install)**:
```json
{
  "mcpServers": {
    "plots": {
      "command": "uvx",
      "args": ["mcp-plots", "--transport", "stdio"]
    }
  }
}
```

4. **Route C — Latest from Git (uvx)**:
```json
{
  "mcpServers": {
    "plots": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mr901/mcp-plots.git@main", "mcp-plots", "--transport", "stdio"]
    }
  }
}
```

5. **Restart Cursor**

### Continue IDE

1. **Open settings**: `~/.continue/config.json`

2. **Add to mcpServers**:
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### Other MCP Clients

Use the same configuration pattern with your client's MCP server configuration.

## Verification

Test the integration with these prompts:

**Basic chart**:
```
Create a bar chart: A=10, B=20, C=15
```

**Real-world example**:
```
Show quarterly revenue as a line chart: Q1=2.4M, Q2=2.7M, Q3=3.1M, Q4=3.8M
```

**Multi-series data**:
```
Create a grouped bar chart comparing sales by region:
North: Product A=100, Product B=150
South: Product A=120, Product B=140
```

## Expected Output

Charts render as interactive Mermaid diagrams directly in your chat interface. No external tools or viewers required.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not found | Ensure `pip install mcp-plots` succeeded and command is in PATH |
| Server not connecting | Verify JSON syntax in config file (no trailing commas) |
| Charts not rendering | Restart MCP client after configuration changes |

## Next Steps

- **Complex data**: See [Integration Guide](integration.md) for advanced configuration
- **Custom charts**: Review [API Reference](api.md) for all available options
- **Production deployment**: Check [Advanced Guide](advanced.md) for scaling considerations

## Performance Notes

- **First run**: May take 2-3 seconds for package initialization
- **Subsequent charts**: Sub-second generation
- **Memory usage**: ~50MB baseline, +5-10MB per active chart session
