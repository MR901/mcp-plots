# MCP Plots Documentation

**Professional data visualization server for Model Context Protocol (MCP) clients**

## Why MCP Plots?

- Visual-first: Mermaid output renders instantly in MCP clients like Cursor
- Simple prompts → charts from plain data, fast iteration
- Multiple setup routes: PyPI, uvx (zero-install), Docker
- Flexible formats: mermaid (default), PNG image, text

## Overview

MCP Plots provides chart generation capabilities via the Model Context Protocol. It renders interactive Mermaid diagrams and static images from structured data using natural language prompts.

**Key Features:**
- 12+ chart types (bar, line, pie, scatter, heatmap, etc.)
- Mermaid-first approach for universal compatibility
- Zero-configuration operation with intelligent defaults
- Extensible architecture for custom chart types

## Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[Quickstart](quickstart.md)** | Get running in 5 minutes | All users |
| **[Integration](integration.md)** | MCP client setup and configuration | Integrators |
| **[API Reference](api.md)** | Complete tool specifications | Developers |
| **[Advanced](advanced.md)** | Architecture, deployment, extension | Power users |

## Quick Usage

Ask in your MCP client:
```
Create a bar chart showing sales: A=100, B=150, C=80
```

Result renders as a Mermaid diagram by default.

## Cursor IDE Integration

**For Cursor IDE Users:**

This repository includes `.cursorrules` that automatically configure Cursor to:
- Render mermaid output visually as diagrams
- Prioritize visual chart rendering over raw syntax
- Use external MCP tool functionality for optimal data visualization

When using this MCP server with Cursor, charts will be automatically rendered visually for the best user experience.

## Supported Chart Types

### Quantitative Data
- `line` - Time series and trend analysis
- `bar` - Categorical comparisons
- `area` - Volume visualization with fill
- `scatter` - Correlation analysis
- `histogram` - Distribution analysis

### Categorical Data
- `pie` - Proportion visualization
- `funnel` - Process flow analysis
- `boxplot` - Statistical distribution

### Relational Data
- `heatmap` - 2D intensity mapping
- `sankey` - Flow diagrams
- `gauge` - KPI visualization
- `radar` - Multi-dimensional comparison

## Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `mermaid` | Text-based diagrams (default) | Universal compatibility, Cursor integration |
| `mcp_image` | Base64 PNG images | High-fidelity visualization |
| `mcp_text` | SVG vector graphics | Scalable web graphics |

## System Requirements

- **Python**: 3.10+
- **MCP Client**: Cursor, Continue, or compatible
- **Dependencies**: matplotlib, pandas, seaborn (auto-installed)

## Installation

```bash
pip install mcp-plots
```

## Basic Usage

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

Then in your MCP client:
```
Create a bar chart showing Q1 sales: Product A=100K, Product B=150K, Product C=80K
```

## Support

- **Issues**: Report via GitHub Issues
- **API Questions**: See [API Reference](api.md)
- **Integration Help**: See [Integration Guide](integration.md)