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
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    AREA = "area"
    BOXPLOT = "boxplot"
    HISTOGRAM = "histogram"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    RADAR = "radar"
    SANKEY = "sankey"
    DASHBOARD = "dashboard"

    @property
    def required_fields(self) -> Set[str]:
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
    DEFAULT = "default"
    DARK = "dark"
    SEABORN = "seaborn"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    SCIENTIFIC = "scientific"

    @property
    def color_palette(self) -> List[str]:
        palettes = {
            "default": [
                "#5470c6",
                "#91cc75",
                "#fac858",
                "#ee6666",
                "#73c0de",
                "#3ba272",
                "#fc8452",
                "#9a60b4",
                "#ea7ccc",
            ],
            "dark": [
                "#4992ff",
                "#7cffb2",
                "#fddd60",
                "#ff6e76",
                "#58d9f9",
                "#05c091",
                "#ff8a45",
                "#8d48e3",
                "#dd79ff",
            ],
            "seaborn": [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
            ],
            "minimal": ["#333333", "#666666", "#999999", "#cccccc", "#e6e6e6"],
            "corporate": ["#003f7f", "#0066cc", "#3399ff", "#66b3ff", "#99ccff"],
            "scientific": [
                "#d73027",
                "#f46d43",
                "#fdae61",
                "#fee08b",
                "#e6f598",
                "#abdda4",
                "#66c2a5",
                "#3288bd",
                "#5e4fa2",
            ],
        }
        return palettes[self.value]


class OutputFormat(Enum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    BASE64 = "base64"
    BUFFER = "buffer"
    MCP_IMAGE = "mcp_image"
    MCP_TEXT = "mcp_text"
    MERMAID = "mermaid"
    HTML = "html"
    JSON = "json"


class DisplayMode(Enum):
    STATIC = "static"
    INTERACTIVE = "interactive"
    CHAT = "chat"
    HYBRID = "hybrid"
    API = "api"
    EMBEDDED = "embedded"


class OutputTarget(Enum):
    MEMORY = "memory"
    FILE = "file"
    CHAT_INLINE = "chat_inline"
    API_RESPONSE = "api_response"
    POPUP_WINDOW = "popup_window"
    CLIPBOARD = "clipboard"
    EMAIL = "email"


@dataclass
class ChartData:
    data: Union[List[Dict[str, Any]], "pd.DataFrame"]
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    category_field: Optional[str] = None
    value_field: Optional[str] = None
    group_field: Optional[str] = None
    size_field: Optional[str] = None
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    name_field: Optional[str] = None
    time_field: Optional[str] = None
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
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
    width: int = 800
    height: int = 600
    title: Optional[str] = None
    x_title: Optional[str] = None
    y_title: Optional[str] = None
    theme: Theme = Theme.DEFAULT
    colors: Optional[List[str]] = None
    background_color: Optional[str] = None
    grid_color: Optional[str] = None
    text_color: Optional[str] = None
    output_format: OutputFormat = OutputFormat.PNG
    output_targets: List[OutputTarget] = field(default_factory=lambda: [OutputTarget.MEMORY])
    display_mode: DisplayMode = DisplayMode.STATIC
    dpi: int = 100
    show_grid: bool = True
    show_legend: bool = True

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width/height must be positive")
        if self.dpi <= 0 or self.dpi > 1200:
            raise ValueError("DPI must be between 1 and 1200")
        
        # Ensure theme is a Theme enum object
        if isinstance(self.theme, str):
            try:
                self.theme = Theme(self.theme)
            except ValueError:
                self.theme = Theme.DEFAULT
        
        if not self.colors:
            self.colors = self.theme.color_palette
