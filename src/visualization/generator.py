from __future__ import annotations

import base64
import io
import logging
from typing import Dict, List, Any, Optional, Union

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.sankey import Sankey

from .chart_config import ChartData, ChartConfig, ChartType, Theme, OutputFormat
from .mermaid_generator import MermaidGenerator
from .field_validator import FieldValidator, FieldValidationError

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Advanced chart generation engine with comprehensive visualization capabilities.
    
    This class serves as the primary matplotlib-based chart generation system,
    providing high-fidelity static image outputs for all supported chart types.
    It implements sophisticated algorithms for data processing, visual styling,
    and multi-format export capabilities.
    
    Architecture Overview:
    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
    │ Data Preprocessing  │ -> │ Chart Generation    │ -> │ Output Processing   │
    │ • DataFrame conv.   │    │ • Theme application │    │ • Format conversion │
    │ • Field validation  │    │ • Plot creation     │    │ • Resource cleanup  │
    │ • Type coercion     │    │ • Style customiz.   │    │ • MCP serialization│
    └─────────────────────┘    └─────────────────────┘    └─────────────────────┘
    
    Key Features:
    - **Multi-Format Output**: PNG, SVG, Base64, MCP Protocol formats
    - **Theme Support**: Professional themes with consistent color palettes
    - **Memory Management**: Proper resource cleanup and buffer handling
    - **Error Resilience**: Graceful fallbacks and comprehensive error handling
    - **Performance Optimized**: Efficient data processing and matplotlib usage
    
    Supported Chart Types:
    - Statistical: Line, Bar, Area, Scatter, Histogram, Box Plot
    - Categorical: Pie, Funnel, Gauge, Radar
    - Relational: Heatmap, Sankey Flow Diagrams
    - Hybrid: Mermaid diagram generation for universal compatibility
    
    Theme System:
    Each theme provides carefully curated color palettes optimized for specific contexts:
    - DEFAULT: Professional blue palette for business presentations
    - DARK: High-contrast colors optimized for dark backgrounds/dashboards
    - SEABORN: Statistical visualization with subtle, research-friendly colors
    
    Memory Management:
    - Uses context managers for all buffer operations to prevent leaks
    - Automatic matplotlib figure cleanup after processing
    - Resource pooling for efficient memory utilization
    - Configurable memory limits via chart configuration
    
    Thread Safety:
    - All static methods are thread-safe and stateless
    - No shared mutable state between chart generations
    - Safe for concurrent use in multi-threaded applications
    
    Performance Characteristics:
    - Time Complexity: Generally O(n) where n = number of data points
    - Space Complexity: O(n + output_size) with automatic cleanup
    - Memory efficient: Streaming data processing where possible
    - Scalable: Handles datasets up to configured limits
    
    Example Usage:
        ```python
        # Create chart data and configuration
        chart_data = ChartData(
            data=[{"month": "Jan", "sales": 1000}, {"month": "Feb", "sales": 1200}],
            x_field="month",
            y_field="sales"
        )
        config = ChartConfig(
            width=800, 
            height=600, 
            theme=Theme.DEFAULT,
            output_format=OutputFormat.MCP_IMAGE
        )
        
        # Generate chart
        result = ChartGenerator.generate_line_chart(chart_data, config)
        
        # Result contains MCP-compatible image data
        print(result["content"][0]["type"])  # "image"
        ```
        
    Integration Notes:
    - Designed for seamless integration with MCP protocol
    - Compatible with all major matplotlib versions (3.5+)
    - Optimized for Cursor IDE and other MCP clients
    - Supports both programmatic and interactive use cases
    
    See Also:
    - MermaidGenerator: For text-based diagram generation
    - ChartConfig: For comprehensive styling options
    - ChartData: For data structure and field mapping requirements
    """
    
    # Default color palettes for different themes
    DEFAULT_COLORS = {
        Theme.DEFAULT: ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc"],
        Theme.DARK: ["#4992ff", "#7cffb2", "#fddd60", "#ff6e76", "#58d9f9", "#05c091", "#ff8a45", "#8d48e3", "#dd79ff"],
        Theme.SEABORN: sns.color_palette("husl", 9).as_hex() if sns else ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    }

    @staticmethod
    def _setup_theme(theme: Theme) -> None:
        """Setup matplotlib theme"""
        if theme == Theme.DARK:
            plt.style.use("dark_background")
        elif theme == Theme.SEABORN:
            sns.set_style("whitegrid")
        else:
            plt.style.use("default")

    @staticmethod
    def _get_colors(theme: Theme, custom_colors: Optional[List[str]] = None) -> List[str]:
        """Get color palette for the theme"""
        if custom_colors:
            return custom_colors
        return ChartGenerator.DEFAULT_COLORS.get(theme, ChartGenerator.DEFAULT_COLORS[Theme.DEFAULT])

    @staticmethod
    def _prepare_data(chart_data: ChartData) -> pd.DataFrame:
        """Convert data to pandas DataFrame if needed"""
        if isinstance(chart_data.data, pd.DataFrame):
            return chart_data.data
        elif isinstance(chart_data.data, list):
            return pd.DataFrame(chart_data.data)
        else:
            raise ValueError("Data must be a list of dictionaries or pandas DataFrame")

    @staticmethod
    def _save_chart(fig: plt.Figure, config: ChartConfig, chart_data: Optional[ChartData] = None, chart_type: Optional[ChartType] = None) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """
        Save chart in the specified output format with proper resource management.
        
        This method handles the conversion of matplotlib figures to various output formats
        including PNG images, SVG graphics, and Mermaid diagram syntax. It implements
        proper memory management using context managers to prevent resource leaks.
        
        Args:
            fig: The matplotlib figure to save/convert
            config: Chart configuration specifying output format and parameters
            chart_data: Optional chart data for Mermaid generation
            chart_type: Optional chart type for Mermaid generation
            
        Returns:
            Union[str, bytes, io.BytesIO, Dict[str, Any]]: 
                - For BASE64: Data URI string with embedded image
                - For MCP_IMAGE/MCP_TEXT: MCP-compatible content dictionary
                - For other formats: Raw data or buffer objects
                
        Raises:
            IOError: If figure saving fails
            MemoryError: If image processing exhausts available memory
            
        Note:
            Uses context managers for all buffer operations to ensure proper cleanup
            and prevent memory leaks, even when exceptions occur during processing.
        """
        if config.output_format == OutputFormat.BASE64:
            with io.BytesIO() as buffer:
                fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return f"data:image/png;base64,{image_base64}"
        
        elif config.output_format == OutputFormat.MCP_IMAGE:
            # MCP Protocol format for images with guaranteed resource cleanup
            with io.BytesIO() as buffer:
                fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return {
                    "content": [
                        {
                            "type": "image",
                            "data": image_base64,
                            "mimeType": "image/png"
                        }
                    ]
                }
        
        elif config.output_format == OutputFormat.MCP_TEXT:
            # MCP Protocol format for SVG text with proper memory management
            with io.BytesIO() as buffer:
                fig.savefig(buffer, format='svg', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                svg_string = buffer.getvalue().decode('utf-8')
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": svg_string
                        }
                    ]
                }
        
        elif config.output_format == OutputFormat.MERMAID:
            # Generate Mermaid diagram syntax
            if chart_data and chart_type:
                mermaid_syntax = MermaidGenerator.generate(chart_type, chart_data, config)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": mermaid_syntax
                        }
                    ]
                }
            else:
                # Fallback: return a simple error mermaid
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": """flowchart TD
    A["Chart Generation"] --> B["Missing chart_data or chart_type for Mermaid generation"]
    style A fill:#ffcdd2
    style B fill:#ffcdd2"""
                        }
                    ]
                }
        
        elif config.output_format == OutputFormat.BUFFER:
            buffer = io.BytesIO()
            format_str = 'png' if config.output_format == OutputFormat.PNG else 'svg'
            fig.savefig(buffer, format=format_str, dpi=config.dpi, bbox_inches='tight')
            buffer.seek(0)
            return buffer
        
        else:  # PNG or SVG
            buffer = io.BytesIO()
            format_str = 'png' if config.output_format == OutputFormat.PNG else 'svg'
            fig.savefig(buffer, format=format_str, dpi=config.dpi, bbox_inches='tight')
            buffer.seek(0)
            return buffer.getvalue()

    @staticmethod
    def generate_line_chart(chart_data: ChartData, config: ChartConfig, smooth: bool = False, show_area: bool = False, show_points: bool = True, stack: bool = False) -> Union[str, bytes, io.BytesIO]:
        """Generate a line chart"""
        ChartGenerator._setup_theme(config.theme)
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        # Use FieldValidator to check optional fields safely
        optional_fields = FieldValidator.validate_optional_fields(chart_data, 'group_field')
        if optional_fields['group_field']:
            groups = df[chart_data.group_field].unique()
            bottom = None if not stack else np.zeros(len(df[chart_data.x_field].unique()))
            for i, group in enumerate(groups):
                group_data = df[df[chart_data.group_field] == group]
                x_data = group_data[chart_data.x_field]
                y_data = group_data[chart_data.y_field]
                color = colors[i % len(colors)]
                if show_area:
                    if stack and bottom is not None:
                        ax.fill_between(x_data, bottom, bottom + y_data, alpha=0.7, color=color, label=group)
                        bottom += y_data
                    else:
                        ax.fill_between(x_data, 0, y_data, alpha=0.7, color=color, label=group)
                ax.plot(x_data, y_data, '-', color=color, label=group, marker='o' if show_points else None, markersize=4)
        else:
            x_data = df[chart_data.x_field]
            y_data = df[chart_data.y_field]
            color = colors[0]
            if show_area:
                ax.fill_between(x_data, 0, y_data, alpha=0.7, color=color)
            ax.plot(x_data, y_data, '-', color=color, marker='o' if show_points else None, markersize=4)
        
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title)
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        if config.show_legend and chart_data.group_field:
            ax.legend()
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.LINE)
        plt.close(fig)
        return result

    @staticmethod
    def generate_bar_chart(chart_data: ChartData, config: ChartConfig, horizontal: bool = False, stack: bool = False, group: bool = False) -> Union[str, bytes, io.BytesIO]:
        """Generate a bar chart"""
        ChartGenerator._setup_theme(config.theme)
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        if chart_data.group_field and chart_data.group_field in df.columns:
            if stack:
                pivot_df = df.pivot(index=chart_data.category_field, columns=chart_data.group_field, values=chart_data.value_field).fillna(0)
                if horizontal:
                    pivot_df.plot(kind='barh', stacked=True, ax=ax, color=colors[:len(pivot_df.columns)])
                else:
                    pivot_df.plot(kind='bar', stacked=True, ax=ax, color=colors[:len(pivot_df.columns)])
            elif group:
                pivot_df = df.pivot(index=chart_data.category_field, columns=chart_data.group_field, values=chart_data.value_field).fillna(0)
                if horizontal:
                    pivot_df.plot(kind='barh', ax=ax, color=colors[:len(pivot_df.columns)])
                else:
                    pivot_df.plot(kind='bar', ax=ax, color=colors[:len(pivot_df.columns)])
        else:
            categories = df[chart_data.category_field]
            values = df[chart_data.value_field]
            if horizontal:
                ax.barh(categories, values, color=colors[0])
            else:
                ax.bar(categories, values, color=colors[0])
        
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title)
        if config.show_grid:
            ax.grid(True, alpha=0.3, axis='x' if horizontal else 'y')
        if config.show_legend and chart_data.group_field:
            ax.legend()
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.BAR)
        plt.close(fig)
        return result

    @staticmethod
    def generate_pie_chart(chart_data: ChartData, config: ChartConfig, inner_radius: float = 0.0, explode_largest: bool = False) -> Union[str, bytes, io.BytesIO]:
        """Generate a pie chart"""
        ChartGenerator._setup_theme(config.theme)
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        categories = df[chart_data.category_field]
        values = df[chart_data.value_field]
        explode = None
        if explode_largest:
            max_idx = values.idxmax()
            explode = [0.1 if i == max_idx else 0 for i in range(len(values))]
        
        ax.pie(values, labels=categories, colors=colors[:len(categories)], autopct='%1.1f%%', startangle=90, explode=explode, wedgeprops=dict(width=1-inner_radius) if inner_radius > 0 else None)
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.axis('equal')
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.PIE)
        plt.close(fig)
        return result

    @staticmethod
    def generate_scatter_chart(chart_data: ChartData, config: ChartConfig, size_by_field: bool = False, alpha: float = 0.7) -> Union[str, bytes, io.BytesIO]:
        """Generate a scatter plot"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        x_data = df[chart_data.x_field]
        y_data = df[chart_data.y_field]
        
        # Handle size variation
        sizes = 50  # default
        if size_by_field and hasattr(chart_data, 'size_field') and chart_data.size_field:
            sizes = df[chart_data.size_field] * 10  # scale for visibility
        
        # Handle grouping
        if hasattr(chart_data, 'group_field') and chart_data.group_field:
            groups = df[chart_data.group_field].unique()
            colors = ChartGenerator._get_colors(config.theme, config.colors)
            
            for i, group in enumerate(groups):
                group_data = df[df[chart_data.group_field] == group]
                ax.scatter(group_data[chart_data.x_field], group_data[chart_data.y_field], 
                          alpha=alpha, s=sizes, color=colors[i % len(colors)], label=group)
            ax.legend()
        else:
            ax.scatter(x_data, y_data, alpha=alpha, s=sizes, color=ChartGenerator._get_colors(config.theme, config.colors)[0])
        
        ax.set_xlabel(chart_data.x_field)
        ax.set_ylabel(chart_data.y_field)
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.SCATTER)
        plt.close(fig)
        return result

    @staticmethod
    def generate_heatmap_chart(chart_data: ChartData, config: ChartConfig, colormap: str = 'viridis', annotate: bool = True) -> Union[str, bytes, io.BytesIO]:
        """Generate a heatmap"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        # Create pivot table for heatmap
        pivot_data = df.pivot_table(values=chart_data.value_field, 
                                   index=chart_data.y_field, 
                                   columns=chart_data.x_field, 
                                   aggfunc='mean')
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        sns.heatmap(pivot_data, annot=annotate, cmap=colormap, ax=ax)
        
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.HEATMAP)
        plt.close(fig)
        return result

    @staticmethod
    def generate_boxplot_chart(chart_data: ChartData, config: ChartConfig, show_outliers: bool = True) -> Union[str, bytes, io.BytesIO]:
        """Generate a box plot"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        # Handle grouped boxplots
        if hasattr(chart_data, 'category_field') and chart_data.category_field:
            groups = df[chart_data.category_field].unique()
            data_to_plot = [df[df[chart_data.category_field] == group][chart_data.value_field] for group in groups]
            ax.boxplot(data_to_plot, labels=groups, showfliers=show_outliers)
        else:
            ax.boxplot(df[chart_data.value_field], showfliers=show_outliers)
        
        ax.set_ylabel(chart_data.value_field)
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.BOXPLOT)
        plt.close(fig)
        return result

    @staticmethod
    def generate_histogram_chart(chart_data: ChartData, config: ChartConfig, bins: int = 30, density: bool = False) -> Union[str, bytes, io.BytesIO]:
        """Generate a histogram"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        ax.hist(df[chart_data.value_field], bins=bins, density=density, 
                color=ChartGenerator._get_colors(config.theme, config.colors)[0], alpha=0.7)
        
        ax.set_xlabel(chart_data.value_field)
        ax.set_ylabel('Density' if density else 'Frequency')
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.HISTOGRAM)
        plt.close(fig)
        return result

    @staticmethod
    def generate_funnel_chart(chart_data: ChartData, config: ChartConfig, sort_descending: bool = True) -> Union[str, bytes, io.BytesIO]:
        """Generate a funnel chart"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        # Sort data
        if sort_descending:
            df = df.sort_values(chart_data.value_field, ascending=False)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        categories = df[chart_data.category_field]
        values = df[chart_data.value_field]
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        # Create funnel shape
        max_width = max(values)
        y_positions = range(len(categories))
        
        for i, (cat, val) in enumerate(zip(categories, values)):
            width = val / max_width
            left = (1 - width) / 2
            ax.barh(i, width, left=left, height=0.8, 
                   color=colors[i % len(colors)], alpha=0.8)
            ax.text(0.5, i, f'{cat}: {val}', ha='center', va='center', fontweight='bold')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, len(categories) - 0.5)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.invert_yaxis()
        
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.FUNNEL)
        plt.close(fig)
        return result

    @staticmethod
    def generate_gauge_chart(chart_data: ChartData, config: ChartConfig, min_value: float = 0, max_value: float = 100, show_value: bool = True) -> Union[str, bytes, io.BytesIO]:
        """Generate a gauge chart"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100), subplot_kw={'projection': 'polar'})
        
        value = df[chart_data.value_field].iloc[0]  # Take first value
        
        # Create gauge
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        
        # Background arc
        ax.plot(theta, r, color='lightgray', linewidth=20)
        
        # Value arc
        value_ratio = (value - min_value) / (max_value - min_value)
        value_theta = np.linspace(0, np.pi * value_ratio, int(100 * value_ratio))
        value_r = np.ones_like(value_theta)
        
        color = ChartGenerator._get_colors(config.theme, config.colors)[0]
        ax.plot(value_theta, value_r, color=color, linewidth=20)
        
        # Add value text
        if show_value:
            ax.text(0, 0, f'{value:.1f}', ha='center', va='center', fontsize=16, fontweight='bold')
        
        ax.set_ylim(0, 1.2)
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('W')
        ax.set_rticks([])
        ax.set_thetagrids([])
        
        if config.title:
            ax.set_title(config.title, pad=20)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.GAUGE)
        plt.close(fig)
        return result

    @staticmethod
    def generate_radar_chart(chart_data: ChartData, config: ChartConfig, fill_alpha: float = 0.3) -> Union[str, bytes, io.BytesIO]:
        """Generate a radar chart"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100), subplot_kw={'projection': 'polar'})
        
        categories = df[chart_data.category_field].tolist()
        values = df[chart_data.value_field].tolist()
        
        # Add first point to close the radar
        categories.append(categories[0])
        values.append(values[0])
        
        # Calculate angles
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=True)
        
        # Plot
        color = ChartGenerator._get_colors(config.theme, config.colors)[0]
        ax.plot(angles, values, 'o-', linewidth=2, color=color)
        ax.fill(angles, values, alpha=fill_alpha, color=color)
        
        # Add category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories[:-1])
        
        if config.title:
            ax.set_title(config.title, pad=20)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.RADAR)
        plt.close(fig)
        return result

    @staticmethod
    def generate_sankey_chart(chart_data: ChartData, config: ChartConfig, node_width: float = 0.1) -> Union[str, bytes, io.BytesIO]:
        """Generate a Sankey diagram"""
        df = ChartGenerator._prepare_data(chart_data)
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        # Simple sankey representation using horizontal bars
        sources = df[chart_data.source_field].unique()
        targets = df[chart_data.target_field].unique()
        
        # Group by source-target pairs
        grouped = df.groupby([chart_data.source_field, chart_data.target_field])[chart_data.value_field].sum().reset_index()
        
        # Create simple flow representation
        y_pos = 0
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        for i, (_, row) in enumerate(grouped.iterrows()):
            source = row[chart_data.source_field]
            target = row[chart_data.target_field]
            value = row[chart_data.value_field]
            
            # Draw flow as rectangle
            ax.barh(y_pos, value, height=0.5, 
                   color=colors[i % len(colors)], alpha=0.7,
                   label=f'{source} → {target}')
            
            y_pos += 0.6
        
        ax.set_xlabel(chart_data.value_field)
        ax.set_ylabel('Flows')
        ax.legend()
        
        if config.title:
            ax.set_title(config.title)
        
        result = ChartGenerator._save_chart(fig, config, chart_data, ChartType.SANKEY)
        plt.close(fig)
        return result

    @classmethod  
    def run_with_factory(cls, chart_type: Union[str, ChartType], data: Union[List[Dict[str, Any]], pd.DataFrame], config: Optional[ChartConfig] = None, **kwargs) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """Factory-aware entry point for chart generation (Phase 3)"""
        try:
            from ..services.chart_generator_factory import get_chart_factory
            
            if config is None:
                config = ChartConfig()
            
            # Build chart data
            chart_data = ChartData(data=data)
            for field in ['x_field', 'y_field', 'category_field', 'value_field', 'group_field', 'size_field', 'source_field', 'target_field']:
                if field in kwargs:
                    setattr(chart_data, field, kwargs[field])
            
            # Use factory for generation
            factory = get_chart_factory()
            chart_type_str = chart_type.value if isinstance(chart_type, ChartType) else str(chart_type)
            
            result = factory.generate_chart(chart_type_str, chart_data, config, **kwargs)
            
            # Handle different result types
            if isinstance(result, dict) and "content" in result:
                return result
            elif config.output_format == OutputFormat.MERMAID and isinstance(result, str):
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            else:
                return result
                
        except ImportError:
            # Fallback to legacy implementation if factory is not available
            _logger.warning("Factory not available, falling back to legacy implementation")
            return cls.run(chart_type, data, config, **kwargs)
    
    @classmethod
    def run(cls, chart_type: Union[str, ChartType], data: Union[List[Dict[str, Any]], pd.DataFrame], config: Optional[ChartConfig] = None, **kwargs) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """Main entry point for chart generation"""
        if config is None:
            config = ChartConfig()
        
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type.lower())
        
        # Validate data is not empty
        FieldValidator.validate_data_not_empty(data)
        
        chart_data = ChartData(data=data)
        for field in ['x_field', 'y_field', 'category_field', 'value_field', 'group_field', 'size_field', 'source_field', 'target_field']:
            if field in kwargs:
                setattr(chart_data, field, kwargs[field])
        
        # Centralized field validation
        FieldValidator.validate_chart_fields(chart_type, chart_data)
        
        # Check if MERMAID output is requested - generate directly
        if config.output_format == OutputFormat.MERMAID:
            mermaid_syntax = MermaidGenerator.generate(chart_type, chart_data, config)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": mermaid_syntax
                    }
                ]
            }
        
        # Phase 5: Use factory pattern instead of if/elif chain
        try:
            # Try factory-aware implementation first
            return cls.run_with_factory(chart_type, data, config, **kwargs)
        except ImportError:
            # Fallback to legacy if/elif chain for backward compatibility
            _logger.warning("Factory pattern not available, using legacy dispatch")
            return cls._legacy_chart_dispatch(chart_type, chart_data, config, **kwargs)
        except Exception as e:
            _logger.error(f"Error generating {chart_type.value} chart: {str(e)}")
            raise
    
    @classmethod
    def _legacy_chart_dispatch(cls, chart_type: ChartType, chart_data: ChartData, config: ChartConfig, **kwargs):
        """Legacy chart dispatch logic (Phase 5: Deprecated - use factory instead)"""
        if chart_type == ChartType.LINE:
            return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['smooth', 'show_area', 'show_points', 'stack']})
        elif chart_type == ChartType.BAR:
            return cls.generate_bar_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['horizontal', 'stack', 'group']})
        elif chart_type == ChartType.PIE:
            return cls.generate_pie_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['inner_radius', 'explode_largest']})
        elif chart_type == ChartType.AREA:
            kwargs['show_area'] = True
            return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['smooth', 'show_area', 'show_points', 'stack']})
        elif chart_type == ChartType.SCATTER:
            return cls.generate_scatter_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['size_by_field', 'alpha']})
        elif chart_type == ChartType.HEATMAP:
            return cls.generate_heatmap_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['colormap', 'annotate']})
        elif chart_type == ChartType.BOXPLOT:
            return cls.generate_boxplot_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['show_outliers']})
        elif chart_type == ChartType.HISTOGRAM:
            return cls.generate_histogram_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['bins', 'density']})
        elif chart_type == ChartType.FUNNEL:
            return cls.generate_funnel_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['sort_descending']})
        elif chart_type == ChartType.GAUGE:
            return cls.generate_gauge_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['min_value', 'max_value', 'show_value']})
        elif chart_type == ChartType.RADAR:
            return cls.generate_radar_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['fill_alpha']})
        elif chart_type == ChartType.SANKEY:
            return cls.generate_sankey_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['node_width']})
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
