# Plots MCP Server

A lightweight Model Context Protocol (MCP) server for data visualization. It exposes tools to render charts (line, bar, pie, scatter, heatmap, etc.) from tabular data and returns MCP-compatible image/text content.

<!-- mcp-name: io.github.MR901/mcp-plots -->

## Why MCP Plots?

- Instant, visual-first charts using Mermaid (renders directly in MCP clients like Cursor)
- Simple prompts to generate charts from plain data
- Zero-setup options via uvx, or install from PyPI/Docker
- Flexible output formats: mermaid (default), PNG image, or text

## Quick Usage

- Ask your MCP client: "Create a bar chart showing sales: A=100, B=150, C=80"
- Default output is Mermaid, so diagrams render instantly in Cursor

## Quick Start

### PyPI Installation (Recommended)
```bash
pip install mcp-plots
mcp-plots  # Start the server
```

### For Cursor Users
1. Install the package: `pip install mcp-plots`
2. Add to your Cursor MCP config (`~/.cursor/mcp.json`):
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
   Alternative (zero-install via uvx + PyPI):
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
3. Restart Cursor
4. Ask: *"Create a bar chart showing sales: A=100, B=150, C=80"*

### Development Installation
```bash
uvx --from git+https://github.com/mr901/mcp-plots.git run-server.py
```

**[Documentation →](docs/README.md)** | **[Quick Start →](docs/quickstart.md)** | **[API Reference →](docs/api.md)**

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

## Setup Routes

### uvx (Recommended)

The easiest way to run the MCP server without managing Python environments:

```bash
# Run directly with uvx (no installation needed)
uvx --from git+https://github.com/mr901/mcp-plots.git run-server.py

# Or install and run the command
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots

# With custom options
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots --port 8080 --log-level DEBUG
```

**Why uvx?**
- **No Environment Management**: Automatically handles Python dependencies
- **Isolated Execution**: Runs in its own virtual environment
- **Always Latest**: Pulls fresh code from repository
- **Zero Setup**: Works immediately without pip install
- **Cross-Platform**: Same command works on Windows, macOS, Linux

### PyPI (Traditional Installation)

1) **Install dependencies**
```bash
pip install -r requirements.txt
```

2) **Run the server (HTTP transport, default port 8000)**
```bash
python -m src --transport streamable-http --host 0.0.0.0 --port 8000 --log-level INFO
```

3) **Run with stdio (for MCP clients that spawn processes)**
```bash
python -m src --transport stdio
```

### Local Development (from source)
```bash
git clone https://github.com/mr901/mcp-plots.git
cd mcp-plots
pip install -e .
python -m src --transport stdio --log-level DEBUG
```

### Docker

```bash
docker build -t mcp-plots .
docker run -p 8000:8000 mcp-plots
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

### Cursor Integration

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

**With uvx (recommended):**
```bash
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots --help

# Examples:
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots --port 8080 --log-level DEBUG
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots --chart-width 1200 --chart-height 800
```

**Traditional Python:**
```bash
python -m src --help

# Examples:
python -m src --transport streamable-http --host 0.0.0.0 --port 8000
python -m src --log-level DEBUG --chart-width 1200 --chart-height 800
```

## Docker

Build image:
```
docker build -t mcp-plots .
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
  mcp-plots
```

## Cursor MCP Integration

### Quick Setup for Cursor

The Plots MCP Server is designed to work seamlessly with Cursor's MCP support. Here's how to integrate it:

#### 1. **Add to Cursor's MCP Configuration**

Add this to your Cursor MCP configuration file (`~/.cursor/mcp.json` or similar):

```json
{
  "mcpServers": {
    "plots": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/mr901/mcp-plots.git@main",
        "mcp-plots",
        "--transport", 
        "stdio"
      ],
      "env": {
        "LOG_LEVEL": "INFO",
        "CHART_DEFAULT_WIDTH": "800",
        "CHART_DEFAULT_HEIGHT": "600"
      }
    }
  }
}
```

#### 2. **Alternative: HTTP Transport**

For HTTP-based integration:

```json
{
  "mcpServers": {
    "plots-http": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/mr901/mcp-plots.git@main", 
        "mcp-plots",
        "--transport", 
        "streamable-http",
        "--host", 
        "127.0.0.1",
        "--port", 
        "8000"
      ]
    }
  }
}
```

#### 3. **Local Development Setup**

For local development (if you have the code cloned):

```json
{
  "mcpServers": {
    "plots-dev": {
      "command": "python",
      "args": ["-m", "src", "--transport", "stdio"],
      "cwd": "/path/to/mcp-plots",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

#### 4. **Verify Integration**

After adding the configuration:
1. **Restart Cursor**
2. **Check MCP connection** in Cursor's MCP panel
3. **Test with a simple chart**:
   ```
   Create a bar chart showing sales data: A=100, B=150, C=80
   ```

### **MERMAID-First Approach**

This server prioritizes **MERMAID output by default** because:
- ✅ **Renders instantly in Cursor** - No external viewers needed
- ✅ **Interactive** - Cursor can analyze and discuss the diagrams  
- ✅ **Lightweight** - Fast generation and display
- ✅ **Scalable** - Vector-based, works at any zoom level

**Chart Types with Native MERMAID Support:**
- `line`, `bar`, `pie`, `area` → `xychart-beta` format
- `histogram` → `xychart-beta` with automatic binning  
- `funnel` → Styled flowchart with color gradients
- `gauge` → Flowchart with color-coded value indicators
- `sankey` → Flow diagrams with source/target styling

## Available Tools

### `render_chart`
Main chart generation tool with MERMAID-first approach.

**Parameters:**
- `chart_type` - Chart type (`line`, `bar`, `pie`, `scatter`, `heatmap`, etc.)
- `data` - List of data objects
- `field_map` - Field mappings (`x_field`, `y_field`, `category_field`, etc.)
- `config_overrides` - Chart configuration overrides
- `output_format` - Output format (`mermaid` [default], `mcp_image`, `mcp_text`)

**Special Modes:**
- `chart_type="help"` - Show available chart types and themes
- `chart_type="suggest"` - Analyze data and suggest field mappings

### `configure_preferences`
Interactive configuration tool for setting user preferences.

**Parameters:**
- `output_format` - Default output format (`mermaid`, `mcp_image`, `mcp_text`)
- `theme` - Default theme (`default`, `dark`, `seaborn`, `minimal`)
- `chart_width` - Default chart width in pixels
- `chart_height` - Default chart height in pixels
- `reset_to_defaults` - Reset all preferences to system defaults

**Features:**
- **Persistent Settings** - Saved to `~/.plots_mcp_config.json`
- **Live Preview** - Shows sample chart with current settings
- **Override Support** - Use `config_overrides` for one-off changes

## Documentation

### Additional Resources
- **[Complete Documentation](docs/README.md)** - Technical documentation hub
- **[Quick Start](docs/quickstart.md)** - 5-minute setup guide
- **[Integration Guide](docs/integration.md)** - MCP client setup and configuration
- **[API Reference](docs/api.md)** - Complete tool specifications and examples
- **[Advanced Guide](docs/advanced.md)** - Architecture, deployment, and development
- **[Sample Prompts](docs/sample-prompts.md)** - Ready-to-use testing examples

### Chart Examples

**Basic Bar Chart:**
```json
{
  "chart_type": "bar",
  "data": [
    {"category": "Sales", "value": 120},
    {"category": "Marketing", "value": 80},
    {"category": "Support", "value": 60}
  ],
  "field_map": {
    "category_field": "category", 
    "value_field": "value"
  }
}
```

**Time Series Line Chart:**
```json
{
  "chart_type": "line",
  "data": [
    {"date": "2024-01", "revenue": 1000},
    {"date": "2024-02", "revenue": 1200},
    {"date": "2024-03", "revenue": 1100}
  ],
  "field_map": {
    "x_field": "date",
    "y_field": "revenue"
  }
}
```

**Funnel Chart:**
```json
{
  "chart_type": "funnel",
  "data": [
    {"stage": "Awareness", "value": 1000},
    {"stage": "Interest", "value": 500}, 
    {"stage": "Purchase", "value": 100}
  ],
  "field_map": {
    "category_field": "stage",
    "value_field": "value"
  }
}
```

## 🔧 Configuration

### Environment Variables
- `MCP_TRANSPORT` - Transport type (`streamable-http` | `stdio`)
- `MCP_HOST` - Host address (default: `0.0.0.0`)
- `MCP_PORT` - Port number (default: `8000`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `MCP_DEBUG` - Enable debug mode (`true` | `false`)
- `CHART_DEFAULT_WIDTH` - Default chart width in pixels (default: `800`)
- `CHART_DEFAULT_HEIGHT` - Default chart height in pixels (default: `600`)
- `CHART_DEFAULT_DPI` - Default chart DPI (default: `100`)
- `CHART_MAX_DATA_POINTS` - Maximum data points per chart (default: `10000`)

### User Preferences
Personal preferences are stored in `~/.plots_mcp_config.json`:
```json
{
  "defaults": {
    "output_format": "mermaid",
    "theme": "default",
    "chart_width": 800,
    "chart_height": 600
  },
  "user_preferences": {
    "output_format": "mcp_image",
    "theme": "dark"
  }
}
```

## 🚀 Advanced Usage

### Custom Themes
Available themes: `default`, `dark`, `seaborn`, `minimal`, `whitegrid`, `darkgrid`, `ticks`

### High-Resolution Charts
```bash
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots \
  --chart-width 1920 \
  --chart-height 1080 \
  --chart-dpi 300
```

### Performance Optimization
- Use `max_data_points` to limit large datasets
- MERMAID output is fastest for quick visualization
- PNG output for high-quality static images
- SVG output for scalable vector graphics

## 🐛 Troubleshooting

### Common Issues

**Issue**: Charts not rendering in Cursor
- **Solution**: Ensure `output_format="mermaid"` (default)
- **Check**: MCP server connection in Cursor

**Issue**: `uvx` command not found
- **Solution**: Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Issue**: Port already in use
- **Solution**: Use different port: `--port 8001`

**Issue**: Large datasets slow
- **Solution**: Sample data or increase `--max-data-points`

### Debug Mode
```bash
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots \
  --debug \
  --log-level DEBUG
```

## 📝 Notes

- Matplotlib runs headless (Agg backend) in the container
- For large datasets, sample your data for responsiveness  
- Chart defaults can be overridden per-request via `config_overrides`
- MERMAID charts render instantly in Cursor for the best user experience
- User preferences persist across sessions and apply to all charts by default
