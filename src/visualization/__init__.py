"""
Visualization Engine Module

Core chart generation functionality with support for multiple chart types,
output formats, and styling options. Provides both matplotlib-based static
charts and Mermaid text-based diagrams.

This module contains:
- Chart configuration classes and enums
- Multi-format chart generator with matplotlib backend
- Mermaid diagram generator for universal compatibility  
- Theme management and color palette support
- Data preprocessing and validation utilities

The visualization engine is designed to be flexible and extensible, supporting
various chart types from simple bar charts to complex Sankey diagrams. All
charts can be rendered in multiple formats to suit different client needs.

Main Components:
    chart_config: Configuration classes, enums, and data structures
    generator: Main chart generation engine using matplotlib
    mermaid_generator: Mermaid diagram generator for text-based output

Supported Chart Types:
    - Line charts for time series data
    - Bar charts for categorical comparisons  
    - Pie charts for proportional data
    - Scatter plots for correlation analysis
    - Heatmaps for 2D data visualization
    - Area charts for volume visualization
    - Box plots for statistical distribution
    - Histograms for frequency distribution
    - Funnel charts for process flow
    - Gauge charts for KPI display
    - Radar charts for multi-dimensional comparison
    - Sankey diagrams for flow visualization
"""

from .chart_config import (
    ChartConfig, ChartData, ChartType, Theme, OutputFormat, 
    DisplayMode, OutputTarget
)
from .generator import ChartGenerator
from .mermaid_generator import MermaidGenerator

__all__ = [
    "ChartConfig", "ChartData", "ChartType", "Theme", "OutputFormat",
    "DisplayMode", "OutputTarget", "ChartGenerator", "MermaidGenerator"
]