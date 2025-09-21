# Plots MCP Server - Output Schema Documentation

This document describes the complete output schema for all tools provided by the Plots MCP Server.

## Response Structure

**Success responses** return data directly in MCP format:
```typescript
interface MCPResponse {
  content: Array<{
    type: "image" | "text"
    data?: string     // For images: base64 PNG data
    text?: string     // For text: SVG or other text content  
    mimeType?: string // For images: "image/png"
  }>
}
```

**Error responses** include status information:
```typescript
interface ErrorResponse {
  status: "error"
  error: string  // Human-readable error message
}
```

## Tool Schemas

### 1. `configure_preferences(...)`

**Purpose**: Interactive configuration tool for setting persistent user preferences

**Parameters**:
```typescript
interface ConfigurePreferencesParams {
  output_format?: "mermaid" | "mcp_image" | "mcp_text"
  theme?: "default" | "dark" | "seaborn" | "minimal" | "corporate" | "scientific"
  chart_width?: number
  chart_height?: number
  reset_to_defaults?: boolean   // Reset all preferences to defaults
}
```

**Success Response**:
```typescript
interface ConfigurePreferencesResponse {
  content: Array<{
    type: "image" | "text"
    data?: string     // For images: base64 PNG data
    text?: string     // For text: markdown content
    mimeType?: string // For images: "image/png"
  }>
}
```

**Features**:
- **Simple & Clean**: Only essential settings (format, theme, size)
- **Persistent Storage**: Saves preferences to `~/.plots_mcp_config.json`
- **Smart Defaults**: Works great out of the box (MERMAID + default theme)
- **Live Sample**: Shows chart with your current settings
- **Easy Reset**: `reset_to_defaults: true` restores all defaults

---

### 2. `render_chart(...)` 

**Purpose**: Multi-purpose chart generation tool with special modes

**Special Modes**:
- `chart_type="help"`: Returns comprehensive help about available options
- `chart_type="suggest"`: Analyzes data and suggests field mappings

**Parameters**:
```typescript
interface RenderChartParams {
  chart_type: string                    // Chart type, "help", or "suggest"
  data?: Array<Record<string, any>>     // Array of data objects (optional for help)
  field_map?: Record<string, string>    // Field mappings (e.g., {"x_field": "month"})
  config_overrides?: Record<string, any> // Chart configuration overrides
  options?: Record<string, any>         // Chart-specific options
  output_format?: string                // "MERMAID" | "MCP_IMAGE" | "MCP_TEXT" (default: MERMAID)
}
```

**Help Mode Response**:
```typescript
interface HelpResponse {
  status: "success"
  help: {
    chart_types: string[]
    themes: string[]
    output_formats: string[]
    special_modes: Record<string, string>
    examples: Record<string, any>
  }
}
```

**Suggest Mode Response**:
```typescript
interface SuggestResponse {
  status: "success"
  suggestions: {
    x_candidates: string[]           // Fields suitable for X-axis
    y_candidates: string[]           // Fields suitable for Y-axis  
    category_candidates: string[]    // Fields suitable for categories
    value_candidates: string[]       // Fields suitable for values
    time_candidates: string[]        // Fields that look like dates/times
    recommended_charts: string[]     // Recommended chart types for this data
  }
}
```

**Field Map Options**:
```typescript
interface FieldMap {
  x_field?: string         // For line, scatter, heatmap charts
  y_field?: string         // For line, scatter, heatmap charts  
  category_field?: string  // For bar, pie, funnel, radar charts
  value_field?: string     // For bar, pie, boxplot, histogram, funnel, gauge, radar, heatmap, sankey
  group_field?: string     // For grouped/series charts
  size_field?: string      // For scatter charts with variable point sizes
  source_field?: string    // For sankey diagrams
  target_field?: string    // For sankey diagrams
  name_field?: string      // For gauge charts
}
```

**Config Overrides**:
```typescript
interface ConfigOverrides {
  width?: number           // Chart width in pixels (default: 800)
  height?: number          // Chart height in pixels (default: 600)
  title?: string           // Chart title
  x_title?: string         // X-axis title
  y_title?: string         // Y-axis title
  theme?: string           // Color theme ("default" | "dark" | "seaborn" | "minimal")
  colors?: string[]        // Custom color palette
  dpi?: number             // Resolution (default: 100)
  show_grid?: boolean      // Show grid lines (default: true)
  show_legend?: boolean    // Show legend (default: true)
}
```

**Chart-Specific Options**:
```typescript
interface ChartOptions {
  // Line charts
  smooth?: boolean         // Smooth lines
  show_area?: boolean      // Fill area under lines
  show_points?: boolean    // Show data points
  stack?: boolean          // Stack multiple series

  // Bar charts  
  horizontal?: boolean     // Horizontal bars
  group?: boolean          // Group multiple series side-by-side

  // Pie charts
  inner_radius?: number    // For donut charts (0.0 to 1.0)
  explode_largest?: boolean // Explode the largest slice

  // Scatter charts
  size_by_field?: boolean  // Vary point size by size_field
  alpha?: number           // Point transparency (0.0 to 1.0)

  // Heatmaps
  colormap?: string        // Matplotlib colormap name
  annotate?: boolean       // Show values in cells

  // Box plots
  show_outliers?: boolean  // Show outlier points

  // Histograms
  bins?: number            // Number of bins
  density?: boolean        // Normalize to show density

  // Funnel charts
  sort_descending?: boolean // Sort values in descending order

  // Gauge charts
  min_value?: number       // Minimum gauge value
  max_value?: number       // Maximum gauge value
  show_value?: boolean     // Show current value

  // Radar charts
  fill_alpha?: number      // Fill transparency (0.0 to 1.0)

  // Sankey diagrams
  node_width?: number      // Width of nodes
}
```

**Success Response (Image Format)**:
```typescript
interface RenderChartImageResponse {
  content: [{
    type: "image"
    data: string      // Base64-encoded PNG image
    mimeType: "image/png"
  }]
}
```

**Success Response (Text/SVG Format)**:
```typescript
interface RenderChartTextResponse {
  content: [{
    type: "text"
    text: string      // SVG markup or other text content
  }]
}
```

**Example Usage**:
```json
{
  "chart_type": "bar",
  "data": [
    {"category": "A", "value": 10, "group": "Q1"},
    {"category": "B", "value": 20, "group": "Q1"},
    {"category": "A", "value": 15, "group": "Q2"}
  ],
  "field_map": {
    "category_field": "category",
    "value_field": "value", 
    "group_field": "group"
  },
  "config_overrides": {
    "width": 1000,
    "height": 600,
    "title": "Sales by Category and Quarter",
    "theme": "dark"
  },
  "options": {
    "group": true
  },
  "output_format": "MCP_IMAGE"
}
```

**Example Response**:
```json
{
  "content": [{
    "type": "image",
    "data": "iVBORw0KGgoAAAANSUhEUgAAAW0AAAGGCAYAAACwgtBj...",
    "mimeType": "image/png"
  }]
}
```

**Usage Examples**:

```javascript
// Get help information
render_chart({chart_type: "help"})

// Analyze data and get suggestions  
render_chart({
  chart_type: "suggest",
  data: [{"month": "Jan", "sales": 100, "region": "North"}]
})

// Create a chart
render_chart({
  chart_type: "bar",
  data: [{"category": "A", "value": 10}],
  field_map: {"category_field": "category", "value_field": "value"},
  config_overrides: {"theme": "dark", "title": "My Chart"}
})
```

---

## Error Response Schema

All tools return errors in a consistent format:

```typescript
interface ErrorResponse {
  status: "error"
  error: string     // Human-readable error message
}
```

**Common Error Examples**:
```json
{
  "status": "error",
  "error": "data must be a non-empty list of objects"
}
```

```json
{
  "status": "error", 
  "error": "Unsupported chart type: invalid_chart"
}
```

```json
{
  "status": "error",
  "error": "Field 'nonexistent_field' not found in data. Available fields: ['name', 'value']"
}
```

---

## Supported Chart Types & Required Fields

| Chart Type | Required Fields | Optional Fields | Description |
|------------|----------------|-----------------|-------------|
| `line` | `x_field`, `y_field` | `group_field` | Line charts for trends over time |
| `bar` | `category_field`, `value_field` | `group_field` | Bar charts for categorical data |
| `pie` | `category_field`, `value_field` | - | Pie charts for proportions |
| `scatter` | `x_field`, `y_field` | `group_field`, `size_field` | Scatter plots for correlations |
| `heatmap` | `x_field`, `y_field`, `value_field` | - | Heatmaps for 2D data intensity |
| `area` | `x_field`, `y_field` | `group_field` | Area charts (filled line charts) |
| `boxplot` | `value_field` | `category_field` | Box plots for distribution analysis |
| `histogram` | `value_field` | - | Histograms for frequency distributions |
| `funnel` | `category_field`, `value_field` | - | Funnel charts for conversion analysis |
| `gauge` | `value_field` | `name_field` | Gauge charts for KPI visualization |
| `radar` | `category_field`, `value_field` | `group_field` | Radar charts for multi-dimensional data |
| `sankey` | `source_field`, `target_field`, `value_field` | - | Sankey diagrams for flow visualization |

---

## MCP Compatibility

This server is fully compatible with **Cursor's MCP image support**:

- ✅ **Correct format**: Uses `content[].type = "image"` with base64 PNG data
- ✅ **Proper MIME type**: Always `"image/png"` for images  
- ✅ **Chat integration**: Images appear directly in Cursor chat
- ✅ **AI analysis**: Vision-enabled models can analyze generated charts
- ✅ **High quality**: Configurable DPI and dimensions for crisp visuals

The default `output_format: "MERMAID"` provides fast, lightweight diagrams that render in Cursor and many other environments.

## 🎯 Simplified Tool Set

We've **consolidated multiple tools into 2 streamlined tools** for better usability:

### **🔧 Available Tools**

1. **`configure_preferences(...)`** → **Interactive configuration** with persistent user preferences
2. **`render_chart(...)`** → **Unified tool** - chart generation, help, and data analysis

**Benefits of the New System**:
- ✅ **Set Once, Use Everywhere** - Configure preferences once, they apply to all charts
- ✅ **Smart Defaults** - Works great out of the box, no setup required
- ✅ **Persistent Storage** - Your preferences are saved between sessions
- ✅ **Interactive Configuration** - See samples with your settings in real-time
- ✅ **Flexible Override** - Per-chart overrides still work when needed
- ✅ **MERMAID default** - Fast, lightweight diagrams that work everywhere
