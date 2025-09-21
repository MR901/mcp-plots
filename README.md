# Plots MCP Server

A lightweight Model Context Protocol (MCP) server for data visualization. It exposes tools to render charts (line, bar, pie, scatter, heatmap, etc.) from tabular data and returns MCP-compatible image/text content.

## Project layout

```
src/
  app/                # Server construction and runtime
    server.py
  capabilities/       # MCP tools and prompts
    tools.py
    prompts.py
  visualization/      # Plotting engines and configurations
    chart_config.py
    generator.py
```

## Requirements

- Python 3.10+
- See `requirements.txt`

## Quickstart (local)

1) Install deps
```
pip install -r requirements.txt
```

2) Run the server (HTTP transport, default port 8000)
```
python -m src --transport streamable-http --host 0.0.0.0 --port 8000 --log-level INFO
```

3) Run with stdio (for MCP clients that spawn processes)
```
python -m src --transport stdio
```

Environment variables (optional):
- `MCP_TRANSPORT` (streamable-http|stdio)
- `MCP_HOST` (default 0.0.0.0)
- `MCP_PORT` (default 8000)
- `LOG_LEVEL` (default INFO)

## Tools

- `list_chart_types()` → returns available chart types
- `list_themes()` → returns available themes
- `suggest_fields(sample_rows)` → suggests field roles based on data samples
- `render_chart(chart_type, data, field_map, config_overrides?, options?, output_format?)` → returns MCP content
- `generate_test_image()` → generates a test image (red circle) to verify MCP image support

### 🎯 Cursor Integration

This MCP server is **fully compatible with Cursor's image support**! When you use the `render_chart` tool:

- **Charts appear directly in chat** - No need to save files or open separate windows
- **AI can analyze your charts** - Vision-enabled models can discuss and interpret your visualizations
- **Perfect MCP format** - Uses the exact base64 PNG format that Cursor expects

The server returns images in the MCP format Cursor requires:
```json
{
  "content": [
    {
      "type": "image", 
      "data": "<base64-encoded-png>",
      "mimeType": "image/png"
    }
  ]
}
```

Example call (pseudo):
```
render_chart(
  chart_type="bar",
  data=[{"category":"A","value":10},{"category":"B","value":20}],
  field_map={"category_field":"category","value_field":"value"},
  config_overrides={"title":"Example Bar","width":800,"height":600,"output_format":"MCP_IMAGE"}
)
```

Return shape (PNG):
```
{
  "status": "success",
  "content": [{"type":"image","data":"<base64>","mimeType":"image/png"}]
}
```

## Configuration

The server can be configured via environment variables or command line arguments:

### Server Settings
- `MCP_TRANSPORT` - Transport type: `streamable-http` or `stdio` (default: `streamable-http`)
- `MCP_HOST` - Host address (default: `0.0.0.0`)
- `MCP_PORT` - Port number (default: `8000`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`)
- `MCP_DEBUG` - Enable debug mode: `true` or `false` (default: `false`)

### Chart Settings
- `CHART_DEFAULT_WIDTH` - Default chart width in pixels (default: `800`)
- `CHART_DEFAULT_HEIGHT` - Default chart height in pixels (default: `600`)
- `CHART_DEFAULT_DPI` - Default chart DPI (default: `100`)
- `CHART_MAX_DATA_POINTS` - Maximum data points per chart (default: `10000`)

### Command Line Usage
```bash
python -m src --help

# Examples:
python -m src --transport streamable-http --host 0.0.0.0 --port 8000
python -m src --log-level DEBUG --chart-width 1200 --chart-height 800
```

## Docker

Build image:
```
docker build -t plots-mcp .
```

Run container with custom configuration:
```bash
docker run --rm -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e LOG_LEVEL=INFO \
  -e CHART_DEFAULT_WIDTH=1000 \
  -e CHART_DEFAULT_HEIGHT=700 \
  -e CHART_DEFAULT_DPI=150 \
  -e CHART_MAX_DATA_POINTS=5000 \
  plots-mcp
```

## Notes

- Matplotlib runs headless (Agg backend) in the container.
- For large datasets, sample your data for responsiveness.
- Chart defaults can be overridden per-request via the `config_overrides` parameter in `render_chart`.
