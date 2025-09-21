# API Reference

Complete specification for MCP Plots tools and capabilities.

## Tool Overview

| Tool | Purpose | Parameters |
|------|---------|------------|
| `render_chart` | Generate charts from data | chart_type, data, field_map, config_overrides, options |
| `configure_preferences` | Manage user preferences | output_format, theme, chart_width, chart_height |

## render_chart

Primary chart generation tool with intelligent data analysis capabilities.

### Signature
```typescript
render_chart(
  chart_type: string,
  data?: Array<Record<string, any>>,
  field_map?: Record<string, string>,
  config_overrides?: Record<string, any>,
  options?: Record<string, any>,
  output_format?: string
): MCPResponse
```

### Parameters

#### chart_type
Chart type identifier or special mode.

**Standard Types**:
- `line` - Time series and trend data
- `bar` - Categorical comparisons  
- `pie` - Proportional data
- `scatter` - Correlation analysis
- `area` - Volume visualization
- `histogram` - Distribution analysis
- `heatmap` - 2D intensity mapping
- `boxplot` - Statistical distribution
- `funnel` - Process flow analysis
- `gauge` - KPI visualization
- `radar` - Multi-dimensional comparison
- `sankey` - Flow diagrams

**Special Modes**:
- `help` - Return available options and examples
- `suggest` - Analyze data and suggest field mappings

#### data
Array of data objects. Each object represents a data point.

**Examples**:
```javascript
// Simple categorical data
[
  {"category": "Q1", "revenue": 1000},
  {"category": "Q2", "revenue": 1200}
]

// Time series data
[
  {"date": "2024-01", "sales": 100, "region": "North"},
  {"date": "2024-01", "sales": 150, "region": "South"}
]

// Multi-dimensional data
[
  {"x": 1, "y": 10, "size": 5, "group": "A"},
  {"x": 2, "y": 15, "size": 8, "group": "B"}
]
```

#### field_map
Maps data fields to chart dimensions.

```typescript
{
  x_field?: string,        // X-axis values (line, scatter, area)
  y_field?: string,        // Y-axis values (line, scatter, area)  
  category_field?: string, // Categories (bar, pie, funnel, radar)
  value_field?: string,    // Numeric values (bar, pie, histogram, gauge)
  group_field?: string,    // Series grouping (multi-series charts)
  size_field?: string,     // Point sizing (scatter)
  source_field?: string,   // Flow source (sankey)
  target_field?: string,   // Flow target (sankey)
  name_field?: string      // Item names (gauge)
}
```

#### config_overrides
Chart configuration overrides.

```typescript
{
  width?: number,          // Chart width (100-5000, default: 800)
  height?: number,         // Chart height (100-5000, default: 600)
  title?: string,          // Chart title
  x_title?: string,        // X-axis label
  y_title?: string,        // Y-axis label
  theme?: string,          // Color theme (default, dark, seaborn)
  colors?: string[],       // Custom color palette
  dpi?: number,            // Image resolution (50-300, default: 100)
  show_grid?: boolean,     // Grid lines (default: true)
  show_legend?: boolean    // Legend display (default: true)
}
```

#### options
Chart-specific rendering options.

```typescript
{
  // Line charts
  smooth?: boolean,        // Smooth line interpolation
  show_area?: boolean,     // Fill area under line
  show_points?: boolean,   // Display data points
  stack?: boolean,         // Stack multiple series
  
  // Bar charts
  horizontal?: boolean,    // Horizontal orientation
  group?: boolean,         // Group multiple series
  
  // Pie charts
  inner_radius?: number,   // Donut chart inner radius (0.0-1.0)
  explode_largest?: boolean, // Explode largest slice
  
  // Scatter plots
  size_by_field?: boolean, // Variable point sizing
  alpha?: number,          // Point transparency (0.0-1.0)
  
  // Heatmaps
  colormap?: string,       // Matplotlib colormap
  annotate?: boolean,      // Show cell values
  
  // Histograms
  bins?: number,           // Number of bins
  density?: boolean,       // Density normalization
  
  // Funnel charts  
  sort_descending?: boolean, // Sort by value
  
  // Gauge charts
  min_value?: number,      // Minimum value
  max_value?: number,      // Maximum value
  show_value?: boolean,    // Display current value
  
  // Radar charts
  fill_alpha?: number,     // Fill transparency (0.0-1.0)
  
  // Sankey diagrams
  node_width?: number      // Node width
}
```

### Response Format

#### Success Response
```typescript
{
  content: Array<{
    type: "text" | "image",
    text?: string,         // Mermaid syntax or SVG markup
    data?: string,         // Base64 PNG data
    mimeType?: string      // "image/png" for images
  }>
}
```

#### Error Response  
```typescript
{
  status: "error",
  error: string            // Human-readable error message
}
```

### Usage Examples

#### Basic Chart
```javascript
render_chart({
  chart_type: "bar",
  data: [
    {"category": "A", "value": 10},
    {"category": "B", "value": 20}
  ],
  field_map: {
    category_field: "category",
    value_field: "value"
  }
})
```

#### Advanced Configuration
```javascript
render_chart({
  chart_type: "line",
  data: [
    {"month": "Jan", "sales": 1000, "region": "North"},
    {"month": "Feb", "sales": 1200, "region": "North"}
  ],
  field_map: {
    x_field: "month",
    y_field: "sales", 
    group_field: "region"
  },
  config_overrides: {
    title: "Sales Trends by Region",
    theme: "dark",
    width: 1000
  },
  options: {
    smooth: true,
    show_points: true
  }
})
```

#### Help Mode
```javascript
render_chart({
  chart_type: "help"
})

// Returns available chart types, themes, and examples
```

#### Data Analysis
```javascript
render_chart({
  chart_type: "suggest",
  data: [{"date": "2024-01", "revenue": 1000, "cost": 800}]
})

// Returns field mapping suggestions based on data structure
```

## configure_preferences

Manage persistent user preferences for chart generation.

### Signature
```typescript
configure_preferences(
  output_format?: string,
  theme?: string,
  chart_width?: number,
  chart_height?: number,
  reset_to_defaults?: boolean
): MCPResponse
```

### Parameters

#### output_format
Default output format for charts.
- `mermaid` (default) - Text-based diagrams
- `mcp_image` - Base64 PNG images  
- `mcp_text` - SVG vector graphics

#### theme
Default color theme.
- `default` - Standard color palette
- `dark` - Dark background theme
- `seaborn` - Statistical visualization theme

#### chart_width / chart_height  
Default dimensions in pixels (100-5000).

#### reset_to_defaults
Reset all preferences to system defaults.

### Response
Returns current configuration with sample chart demonstrating settings.

### Usage Examples

#### Set Preferences
```javascript
configure_preferences({
  output_format: "mcp_image",
  theme: "dark", 
  chart_width: 1000,
  chart_height: 700
})
```

#### Reset Configuration
```javascript
configure_preferences({
  reset_to_defaults: true
})
```

## Data Validation

### Field Requirements

| Chart Type | Required Fields | Optional Fields |
|------------|----------------|------------------|
| `line` | `x_field`, `y_field` | `group_field` |
| `bar` | `category_field`, `value_field` | `group_field` |
| `pie` | `category_field`, `value_field` | |
| `scatter` | `x_field`, `y_field` | `group_field`, `size_field` |
| `area` | `x_field`, `y_field` | `group_field` |
| `histogram` | `value_field` | |
| `heatmap` | `x_field`, `y_field`, `value_field` | |
| `boxplot` | `value_field` | `category_field` |
| `funnel` | `category_field`, `value_field` | |
| `gauge` | `value_field` | `name_field` |
| `radar` | `category_field`, `value_field` | `group_field` |
| `sankey` | `source_field`, `target_field`, `value_field` | |

### Data Constraints

- **Maximum data points**: 10,000 (configurable via `CHART_MAX_DATA_POINTS`)
- **Field names**: Must exist in data objects
- **Numeric fields**: Must contain valid numbers
- **Category fields**: Strings or numbers
- **Missing values**: Filtered automatically

### Error Codes

| Error | Description | Solution |
|--------|-------------|----------|
| `Invalid chart type` | Unsupported chart_type | Use supported chart type or "help" mode |
| `Missing required field` | Required field not in data | Check field_map matches data structure |
| `Empty data` | No data provided | Provide non-empty data array |
| `Invalid field mapping` | Field not found in data | Verify field names match data keys |
| `Too many data points` | Exceeds point limit | Reduce data size or increase limit |

## Performance Characteristics

### Response Times
- **Help/suggest modes**: <50ms
- **Mermaid generation**: 50-200ms
- **Image generation**: 200-800ms
- **Large datasets (1K+ points)**: +100-500ms

### Memory Usage
- **Base server**: ~50MB
- **Per chart request**: +5-10MB temporary
- **Large datasets**: +1MB per 10K points

### Concurrent Requests
- **Default**: Single-threaded processing
- **Recommendation**: Queue requests for high-volume use
