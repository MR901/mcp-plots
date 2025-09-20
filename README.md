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

## Docker

Build image:
```
docker build -t plots-mcp .
```

Run container:
```
docker run --rm -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  plots-mcp
```

## Notes

- Matplotlib runs headless (Agg backend) in the container.
- For large datasets, sample your data for responsiveness.
