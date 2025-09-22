"""
Chart Configuration and Data Structures

This module defines all configuration classes, enums, and data structures used
throughout the visualization system. Provides comprehensive type definitions
for chart types, themes, output formats, and rendering configurations.

Main Components:
- ChartType enum with required field mappings
- Theme enum with predefined color palettes  
- OutputFormat enum for various export options
- DisplayMode and OutputTarget enums for rendering control
- ChartData dataclass for input data management
- ChartConfig dataclass for rendering configuration

The configuration system is designed to be flexible and type-safe, with
sensible defaults and comprehensive validation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore


class ChartType(Enum):
    """
    Supported chart types with automatic field requirement detection.
    
    Each chart type defines the minimum required data fields needed
    for successful chart generation. The visualization system uses
    this information to validate input data and provide helpful
    error messages.
    """
    LINE = "line"          # Time series and trend analysis
    BAR = "bar"            # Categorical comparisons  
    PIE = "pie"            # Proportional data visualization
    SCATTER = "scatter"    # Correlation and relationship analysis
    HEATMAP = "heatmap"    # 2D intensity mapping
    AREA = "area"          # Volume visualization with fill
    BOXPLOT = "boxplot"    # Statistical distribution analysis
    HISTOGRAM = "histogram"  # Frequency distribution
    FUNNEL = "funnel"      # Process flow and conversion rates
    GAUGE = "gauge"        # KPI and metric display
    RADAR = "radar"        # Multi-dimensional comparison
    SANKEY = "sankey"      # Flow and transition diagrams
    DASHBOARD = "dashboard"  # Multi-chart composite view

    @property
    def required_fields(self) -> Set[str]:
        """
        Get the required data field names for this chart type.
        
        Returns:
            Set[str]: Set of field names that must be present in the
                field_map when generating this chart type
        """
        mapping: Dict[ChartType, Set[str]] = {
            ChartType.LINE: {"x_field", "y_field"},
            ChartType.BAR: {"category_field", "value_field"},
            ChartType.PIE: {"category_field", "value_field"},
            ChartType.SCATTER: {"x_field", "y_field"},
            ChartType.HEATMAP: {"x_field", "y_field", "value_field"},
            ChartType.AREA: {"x_field", "y_field"},
            ChartType.BOXPLOT: {"value_field"},
            ChartType.HISTOGRAM: {"value_field"},
            ChartType.FUNNEL: {"category_field", "value_field"},
            ChartType.GAUGE: {"value_field"},
            ChartType.RADAR: {"category_field", "value_field"},
            ChartType.SANKEY: {"source_field", "target_field", "value_field"},
            ChartType.DASHBOARD: set(),
        }
        return mapping.get(self, set())


class Theme(Enum):
    """
    Predefined visual themes with corresponding color palettes.
    
    Each theme provides a carefully curated color palette optimized
    for specific use cases and visual environments. Themes affect
    both chart colors and overall styling.
    """
    DEFAULT = "default"        # Clean, professional blue palette for business
    DARK = "dark"             # Modern dark theme with bright colors for dashboards
    SEABORN = "seaborn"       # Statistical visualization with subtle colors
    MINIMAL = "minimal"       # Understated grayscale for clean, simple charts
    CORPORATE = "corporate"   # Professional blue tones for business reports
    SCIENTIFIC = "scientific" # Color-blind friendly palette for research

    @property
    def color_palette(self) -> List[str]:
        """
        Get the color palette for this theme.
        
        Returns:
            List[str]: List of hex color codes optimized for this theme.
                Colors are ordered for maximum visual separation when
                used sequentially in multi-series charts.
        """
        palettes = {
            "default": [
                "#5470c6",  # Professional blue
                "#91cc75",  # Fresh green
                "#fac858",  # Warm yellow
                "#ee6666",  # Soft red
                "#73c0de",  # Light blue
                "#3ba272",  # Forest green
                "#fc8452",  # Orange
                "#9a60b4",  # Purple
                "#ea7ccc",  # Pink
            ],
            "dark": [
                "#4992ff",  # Bright blue
                "#7cffb2",  # Bright green  
                "#fddd60",  # Bright yellow
                "#ff6e76",  # Bright red
                "#58d9f9",  # Cyan
                "#05c091",  # Teal
                "#ff8a45",  # Bright orange
                "#8d48e3",  # Bright purple
                "#dd79ff",  # Bright pink
            ],
            "seaborn": [
                "#1f77b4",  # Seaborn blue
                "#ff7f0e",  # Seaborn orange
                "#2ca02c",  # Seaborn green
                "#d62728",  # Seaborn red
                "#9467bd",  # Seaborn purple
                "#8c564b",  # Seaborn brown
                "#e377c2",  # Seaborn pink
                "#7f7f7f",  # Seaborn gray
                "#bcbd22",  # Seaborn olive
            ],
            "minimal": ["#333333", "#666666", "#999999", "#cccccc", "#e6e6e6"],
            "corporate": ["#003f7f", "#0066cc", "#3399ff", "#66b3ff", "#99ccff"],
            "scientific": [
                "#d73027",  # Research red
                "#f46d43",  # Research orange-red
                "#fdae61",  # Research orange
                "#fee08b",  # Research yellow-orange
                "#e6f598",  # Research yellow-green
                "#abdda4",  # Research green
                "#66c2a5",  # Research blue-green
                "#3288bd",  # Research blue
                "#5e4fa2",  # Research purple
            ],
        }
        return palettes[self.value]


class OutputFormat(Enum):
    """
    Supported chart output formats for different use cases.
    
    Formats range from static images to interactive content and
    MCP-specific formats optimized for protocol communication.
    """
    PNG = "png"              # Static raster image
    SVG = "svg"              # Scalable vector graphics
    BASE64 = "base64"        # Base64-encoded image data
    BUFFER = "buffer"        # In-memory buffer object
    MCP_IMAGE = "mcp_image"  # MCP protocol image format
    MCP_TEXT = "mcp_text"    # MCP protocol text format (SVG)
    MERMAID = "mermaid"      # Mermaid diagram syntax


class DisplayMode(Enum):
    """
    Chart display modes for different presentation contexts.
    
    Controls how charts are optimized and rendered based on
    the intended display environment and interaction model.
    
    Currently Implemented:
        STATIC: Non-interactive static display (default behavior)
    
    Future Implementation (commented out):
        - INTERACTIVE: Interactive charts with hover/zoom capabilities
        - CHAT: Optimized rendering for chat interface contexts  
        - HYBRID: Mixed static/interactive display modes
        - API: Specialized optimization for API response contexts
        - EMBEDDED: Embedded application integration modes
    """
    STATIC = "static"           # Non-interactive static display (IMPLEMENTED)
    
    # Future implementations (placeholders for development roadmap):
    # INTERACTIVE = "interactive" # Interactive with hover/zoom (TODO: implement)
    # CHAT = "chat"              # Optimized for chat interfaces (TODO: implement)
    # HYBRID = "hybrid"          # Mixed static/interactive (TODO: implement)
    # API = "api"               # API response optimization (TODO: implement)
    # EMBEDDED = "embedded"     # Embedded in other applications (TODO: implement)


class OutputTarget(Enum):
    """
    Destination targets for chart output delivery.
    
    Defines where and how generated charts should be delivered,
    affecting format choices and optimization strategies.
    
    Currently Implemented:
        MEMORY: Keep chart data in application memory (default behavior)
    
    Future Implementation (commented out):
        - FILE: Save charts directly to filesystem
        - CHAT_INLINE: Optimized inline chat display integration
        - API_RESPONSE: Specialized API response payload formatting
        - POPUP_WINDOW: Display charts in popup window interface
        - CLIPBOARD: Copy chart data to system clipboard
        - EMAIL: Format charts for email attachment delivery
    """
    MEMORY = "memory"              # Keep in application memory (IMPLEMENTED)
    
    # Future implementations (placeholders for development roadmap):
    # FILE = "file"                  # Save to filesystem (TODO: implement)
    # CHAT_INLINE = "chat_inline"    # Inline chat display (TODO: implement)
    # API_RESPONSE = "api_response"  # API response payload (TODO: implement)
    # POPUP_WINDOW = "popup_window"  # Display in popup window (TODO: implement)
    # CLIPBOARD = "clipboard"        # Copy to system clipboard (TODO: implement)
    # EMAIL = "email"               # Email attachment (TODO: implement)


@dataclass
class ChartData:
    """
    Container for chart input data and field mappings.
    
    Encapsulates the data to be visualized along with field mappings
    that define how data columns should be used in the chart. Supports
    both pandas DataFrames and list-of-dictionaries formats.
    
    Attributes:
        data: The actual data to visualize (DataFrame or list of dicts)
        x_field: Column name for x-axis values (line, scatter, area charts)
        y_field: Column name for y-axis values (line, scatter, area charts)
        category_field: Column name for categorical grouping (bar, pie charts)
        value_field: Column name for numeric values (bar, pie, histogram charts)
        group_field: Column name for series grouping (multi-series charts)
        size_field: Column name for bubble/point sizes (scatter plots)
        source_field: Column name for flow source (Sankey flow diagrams)
        target_field: Column name for flow target (Sankey flow diagrams)
        data_id: Unique identifier for this data instance (metadata)
        created_at: Timestamp when data was created (metadata)
        
    Future Implementation (commented out):
        - name_field: Column name for entity names (TODO: implement)
        - time_field: Column name for temporal data (TODO: implement)
    """
    data: Union[List[Dict[str, Any]], "pd.DataFrame"]
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    category_field: Optional[str] = None
    value_field: Optional[str] = None
    group_field: Optional[str] = None
    size_field: Optional[str] = None
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    
    # Future implementations (placeholders for development roadmap):
    # name_field: Optional[str] = None      # TODO: implement entity naming support
    # time_field: Optional[str] = None      # TODO: implement temporal data support
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate data format and content after initialization."""
        if pd and isinstance(self.data, pd.DataFrame):
            if self.data.empty:
                raise ValueError("DataFrame is empty")
        elif isinstance(self.data, list):
            if not self.data or not isinstance(self.data[0], dict):
                raise ValueError("Data must be a non-empty list of dicts")
        else:
            raise TypeError("Data must be a pandas DataFrame or list of dictionaries")


@dataclass
class ChartConfig:
    """
    Comprehensive configuration for chart generation and rendering.
    
    Defines all aspects of chart appearance, behavior, and output format.
    Provides sensible defaults while allowing fine-grained control over
    every visual element. Automatically validates settings and applies
    theme-based defaults where appropriate.
    
    Attributes:
        width: Chart width in pixels (must be positive)
        height: Chart height in pixels (must be positive)
        title: Main chart title (optional)
        x_title: X-axis label (optional)
        y_title: Y-axis label (optional)
        theme: Visual theme with predefined color palette
        colors: Custom color list (overrides theme colors if provided)
        output_format: Format for chart output (PNG, SVG, Mermaid, etc.)
        dpi: Resolution for raster outputs (1-1200, higher = better quality)
        show_grid: Whether to display background grid lines
        show_legend: Whether to display chart legend
        
    Limited Implementation (placeholders):
        output_targets: List of delivery targets (currently only MEMORY supported)
        display_mode: Optimization mode (currently only STATIC supported)
        
    Future Implementation (commented out):
        - background_color: Chart background color customization (TODO: implement)
        - grid_color: Grid line color customization (TODO: implement)
        - text_color: Text and label color customization (TODO: implement)
    """
    width: int = 800
    height: int = 600
    title: Optional[str] = None
    x_title: Optional[str] = None
    y_title: Optional[str] = None
    theme: Theme = Theme.DEFAULT
    colors: Optional[List[str]] = None
    
    # Future implementations (placeholders for development roadmap):
    # background_color: Optional[str] = None   # TODO: implement custom background colors
    # grid_color: Optional[str] = None         # TODO: implement custom grid colors  
    # text_color: Optional[str] = None         # TODO: implement custom text colors
    
    output_format: OutputFormat = OutputFormat.PNG
    output_targets: List[OutputTarget] = field(default_factory=lambda: [OutputTarget.MEMORY])
    display_mode: DisplayMode = DisplayMode.STATIC
    dpi: int = 100
    show_grid: bool = True
    show_legend: bool = True

    def __post_init__(self) -> None:
        """
        Validate configuration and apply theme-based defaults.
        
        Performs comprehensive validation of all settings and automatically
        applies theme-based color palettes if custom colors aren't provided.
        Ensures theme is properly converted from string if needed.
        
        Raises:
            ValueError: If width/height are non-positive or DPI is out of range
        """
        # Validate dimensions
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width/height must be positive")
        if self.dpi <= 0 or self.dpi > 1200:
            raise ValueError("DPI must be between 1 and 1200")
        
        # Ensure theme is a Theme enum object (handle string input)
        if isinstance(self.theme, str):
            try:
                self.theme = Theme(self.theme)
            except ValueError:
                self.theme = Theme.DEFAULT
        
        # Apply theme-based color palette if no custom colors provided
        if not self.colors:
            self.colors = self.theme.color_palette
