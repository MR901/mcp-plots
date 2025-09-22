# Integration Guide

Complete guide for integrating MCP Plots with any MCP-compatible client.

## Configuration Patterns

### Basic Configuration
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

### Production Configuration
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": [
        "--transport", "stdio",
        "--log-level", "INFO"
      ],
      "env": {
        "CHART_DEFAULT_WIDTH": "1000",
        "CHART_DEFAULT_HEIGHT": "700",
        "CHART_DEFAULT_DPI": "150"
      }
    }
  }
}
```

### Development Configuration
```json
{
  "mcpServers": {
    "plots-dev": {
      "command": "mcp-plots",
      "args": [
        "--transport", "stdio",
        "--log-level", "DEBUG"
      ],
      "env": {
        "MCP_DEBUG": "true"
      }
    }
  }
}
```

## Client-Specific Setup

### Cursor IDE

**Config location**: `~/.cursor/mcp.json` or `~/.config/cursor/mcp.json`

**Recommended settings**:
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

**Chart rendering**: Mermaid diagrams render automatically in chat interface.

### Continue IDE

**Config location**: `~/.continue/config.json`

**Integration**: Add to existing `mcpServers` section or create new section.

### Generic MCP Client

**Transport options**:
- `stdio` (recommended): Direct process communication
- `streamable-http`: Network-based communication

**HTTP mode setup**:
```json
{
  "mcpServers": {
    "plots": {
      "command": "mcp-plots",
      "args": [
        "--transport", "streamable-http",
        "--host", "127.0.0.1",
        "--port", "8000"
      ]
    }
  }
}
```

## Environment Variables

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

## Command Line Options

```bash
mcp-plots [options]
```

**Transport options**:
- `--transport {stdio,streamable-http}` - Communication method
- `--host HOST` - HTTP bind address (HTTP mode only)
- `--port PORT` - HTTP listen port (HTTP mode only)

**Chart defaults**:
- `--chart-width WIDTH` - Default chart width
- `--chart-height HEIGHT` - Default chart height  
- `--chart-dpi DPI` - Default image resolution

**System options**:
- `--log-level LEVEL` - Logging verbosity
- `--debug` - Enable debug mode
- `--max-data-points N` - Data point limit

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

## Performance Optimization

### Large Datasets
```json
{
  "env": {
    "CHART_MAX_DATA_POINTS": "50000"
  }
}
```

### Memory Management
- **Baseline usage**: ~50MB
- **Per chart session**: +5-10MB  
- **Large datasets**: +1MB per 10K data points

### Rendering Performance
- **Mermaid**: <100ms (recommended)
- **PNG generation**: 200-500ms
- **SVG generation**: 100-300ms

## Security Considerations

### Network Mode
- HTTP server binds to localhost by default
- No authentication mechanism (design for localhost use)
- Consider firewall rules for multi-user environments

### Data Handling
- No data persistence (memory-only processing)
- No external network requests
- Temporary files cleaned automatically

## Error Handling

### Common Issues

**Connection failures**:
```bash
# Test server manually
mcp-plots --transport stdio --log-level DEBUG
```

**Invalid data format**:
- Server returns structured error messages
- Check field mappings match your data structure

**Memory issues**:
- Reduce `CHART_MAX_DATA_POINTS`
- Use data sampling for large datasets

### Debugging

**Enable debug logging**:
```json
{
  "env": {
    "LOG_LEVEL": "DEBUG",
    "MCP_DEBUG": "true"
  }
}
```

**Test configuration**:
```bash
# Validate JSON syntax
cat ~/.cursor/mcp.json | python -m json.tool

# Test server startup
mcp-plots --help
```

## Integration Testing

### Automated Tests
```bash
# Install with dev dependencies
pip install mcp-plots[dev]

# Run integration tests
python -m pytest tests/integration/
```

### Manual Verification
```javascript
// Test basic functionality
render_chart({
  chart_type: "help"
})

// Test data processing  
render_chart({
  chart_type: "suggest",
  data: [{"x": 1, "y": 2}, {"x": 2, "y": 4}]
})

// Test chart generation
render_chart({
  chart_type: "bar",
  data: [{"category": "A", "value": 10}],
  field_map: {"category_field": "category", "value_field": "value"}
})
```
