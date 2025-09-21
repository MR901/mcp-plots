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

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Advanced chart generation class with support for multiple chart types
    and flexible configuration options.
    """
    
    # Default color palettes for different themes
    DEFAULT_COLORS = {
        Theme.DEFAULT: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
        Theme.DARK: ['#4992ff', '#7cffb2', '#fddd60', '#ff6e76', '#58d9f9', '#05c091', '#ff8a45', '#8d48e3', '#dd79ff'],
        Theme.SEABORN: sns.color_palette("husl", 9).as_hex() if sns else ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    }

    @staticmethod
    def _setup_theme(theme: Theme) -> None:
        """Setup matplotlib theme"""
        if theme == Theme.DARK:
            plt.style.use('dark_background')
        elif theme == Theme.SEABORN:
            sns.set_style("whitegrid")
        else:
            plt.style.use('default')

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
        """Save chart in the specified format"""
        if config.output_format == OutputFormat.BASE64:
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            return f"data:image/png;base64,{image_base64}"
        
        elif config.output_format == OutputFormat.MCP_IMAGE:
            # MCP Protocol format for images
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
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
            # MCP Protocol format for SVG text
            buffer = io.BytesIO()
            fig.savefig(buffer, format='svg', dpi=config.dpi, bbox_inches='tight')
            buffer.seek(0)
            svg_string = buffer.getvalue().decode('utf-8')
            buffer.close()
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
        
        if chart_data.group_field and chart_data.group_field in df.columns:
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

    @classmethod
    def run(cls, chart_type: Union[str, ChartType], data: Union[List[Dict[str, Any]], pd.DataFrame], config: Optional[ChartConfig] = None, **kwargs) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """Main entry point for chart generation"""
        if config is None:
            config = ChartConfig()
        
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type.lower())
        
        chart_data = ChartData(data=data)
        for field in ['x_field', 'y_field', 'category_field', 'value_field', 'group_field', 'size_field']:
            if field in kwargs:
                setattr(chart_data, field, kwargs[field])
        
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
        
        # Otherwise, proceed with matplotlib-based generation
        try:
            if chart_type == ChartType.LINE:
                return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['smooth', 'show_area', 'show_points', 'stack']})
            elif chart_type == ChartType.BAR:
                return cls.generate_bar_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['horizontal', 'stack', 'group']})
            elif chart_type == ChartType.PIE:
                return cls.generate_pie_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['inner_radius', 'explode_largest']})
            elif chart_type == ChartType.AREA:
                kwargs['show_area'] = True
                return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() if k in ['smooth', 'show_area', 'show_points', 'stack']})
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
        except Exception as e:
            _logger.error(f"Error generating {chart_type.value} chart: {str(e)}")
            raise
