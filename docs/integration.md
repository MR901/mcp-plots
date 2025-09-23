# Integration Guide

Complete guide for integrating MCP Plots with any MCP-compatible client.

## Setup Routes (Choose One)

### 1) Cursor IDE (PyPI, simplest)
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

### 2) Cursor IDE (uvx, zero-install)
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

### 3) Cursor IDE (latest from Git with uvx)
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

### 4) HTTP transport (any MCP client)
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": ["--transport", "streamable-http", "--host", "127.0.0.1", "--port", "8000"]
    }
  }
}
```

## Client-Specific Setup

### Cursor IDE
- Config file: `~/.cursor/mcp.json` (or `~/.config/cursor/mcp.json`)
- Mermaid charts render visually in chat automatically

### Continue IDE
- Config file: `~/.continue/config.json`
- Add an entry under `mcpServers`

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `streamable-http` | Communication protocol |
| `MCP_HOST` | `0.0.0.0` | HTTP server bind address |
| `MCP_PORT` | `8000` | HTTP server port |
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG/INFO/WARNING/ERROR) |
| `CHART_DEFAULT_WIDTH` | `800` | Default chart width (pixels) |
| `CHART_DEFAULT_HEIGHT` | `600` | Default chart height (pixels) |
| `CHART_DEFAULT_DPI` | `100` | Default image resolution |
| `CHART_MAX_DATA_POINTS` | `10000` | Maximum data points per chart |

#### Examples

Cursor config with environment overrides:
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": ["--transport", "stdio"],
      "env": {
        "LOG_LEVEL": "INFO",
        "CHART_DEFAULT_WIDTH": "1000",
        "CHART_DEFAULT_HEIGHT": "700",
        "CHART_DEFAULT_DPI": "150"
      }
    }
  }
}
```

Shell exports (HTTP mode):
```bash
export MCP_TRANSPORT=streamable-http
export MCP_HOST=127.0.0.1
export MCP_PORT=8000
export LOG_LEVEL=DEBUG
export CHART_DEFAULT_WIDTH=1200
export CHART_DEFAULT_HEIGHT=800
export CHART_DEFAULT_DPI=150
mcp-plots
```

Docker run with environment variables:
```bash
docker run --rm -p 8000:8000 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HOST=0.0.0.0 \
  -e MCP_PORT=8000 \
  -e LOG_LEVEL=INFO \
  -e CHART_DEFAULT_WIDTH=1000 \
  -e CHART_DEFAULT_HEIGHT=700 \
  -e CHART_DEFAULT_DPI=150 \
  mcp-plots
```

### Command Line Options

```bash
mcp-plots [options]
```

- `--transport {stdio,streamable-http}`
- `--host HOST` (HTTP mode)
- `--port PORT` (HTTP mode)
- `--chart-width WIDTH`
- `--chart-height HEIGHT`
- `--chart-dpi DPI`
- `--log-level LEVEL`
- `--debug`
- `--max-data-points N`

## Data Input Formats

### Basic Arrays
```javascript
// Simple category-value pairs
[
  {"category": "A", "value": 10},
  {"category": "B", "value": 20}
]
```

### Time Series
```javascript
// Date-based data
[
  {"date": "2024-01-01", "revenue": 1000, "costs": 800},
  {"date": "2024-02-01", "revenue": 1200, "costs": 900}
]
```

### Multi-dimensional
```javascript
// Grouped data
[
  {"region": "North", "product": "A", "sales": 100},
  {"region": "North", "product": "B", "sales": 150},
  {"region": "South", "product": "A", "sales": 120}
]
```

## Field Mapping

| Field Type | Usage | Chart Types |
|------------|--------|-------------|
| `x_field` | X-axis values | line, scatter, area |
| `y_field` | Y-axis values | line, scatter, area |
| `category_field` | Categories | bar, pie, funnel |
| `value_field` | Numeric values | bar, pie, histogram |
| `group_field` | Series grouping | All multi-series charts |
| `size_field` | Point sizing | scatter |

## Output Format Control

### Default (Mermaid)
```javascript
{
  "chart_type": "bar",
  "output_format": "mermaid"  // or omit for default
}
```

### High-Resolution Images
```javascript
{
  "chart_type": "bar", 
  "output_format": "mcp_image",
  "config_overrides": {
    "width": 1200,
    "height": 800,
    "dpi": 200
  }
}
```

## Performance & Security

### Performance
- Mermaid: <100ms (recommended for iterative workflows)
- PNG generation: 200–500ms
- SVG generation: 100–300ms
- Memory: ~50MB baseline, +5–10MB per active chart

### Security
- HTTP server binds to localhost by default
- No data persistence; memory-only processing
- No outbound network requests

## Troubleshooting

```bash
# Validate JSON syntax
cat ~/.cursor/mcp.json | python -m json.tool

# Test server startup
mcp-plots --help

# Debug logging
mcp-plots --transport stdio --log-level DEBUG
```

## Integration Testing

```javascript
// Basic functionality
render_chart({ chart_type: "help" })

// Data analysis
render_chart({ chart_type: "suggest", data: [{"x": 1, "y": 2}] })

// Chart generation
render_chart({
  chart_type: "bar",
  data: [{"category": "A", "value": 10}],
  field_map: { category_field: "category", value_field: "value" }
})
```
