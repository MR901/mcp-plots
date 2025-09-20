
import base64
import io
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.sankey import Sankey

# Import the new configuration system
try:
    from .chart_config import (
        ChartData, ChartConfig, ChartType, Theme, OutputFormat, 
        DisplayMode, OutputTarget
    )
except ImportError:
    # Fallback for direct execution
    import chart_config
    ChartData = chart_config.ChartData
    ChartConfig = chart_config.ChartConfig
    ChartType = chart_config.ChartType
    Theme = chart_config.Theme
    OutputFormat = chart_config.OutputFormat
    DisplayMode = chart_config.DisplayMode
    OutputTarget = chart_config.OutputTarget

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Advanced chart generation class with support for multiple chart types
    and flexible configuration options.
    
    Provides static methods for generating various types of charts with
    comprehensive customization capabilities.
    """
    
    # Global enhanced generator instance (if available)
    _enhanced_generator = None

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
    def _save_chart(fig: plt.Figure, config: ChartConfig) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
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
    def generate_line_chart(
        chart_data: ChartData,
        config: ChartConfig,
        smooth: bool = False,
        show_area: bool = False,
        show_points: bool = True,
        stack: bool = False
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a line chart
        
        Args:
            chart_data: Chart data with x_field, y_field, and optional group_field
            config: Chart configuration
            smooth: Whether to smooth the lines
            show_area: Whether to fill area under lines
            show_points: Whether to show data points
            stack: Whether to stack multiple series
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        if chart_data.group_field and chart_data.group_field in df.columns:
            # Multiple series
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
                
                line_style = '-' if not smooth else '-'
                ax.plot(x_data, y_data, line_style, color=color, label=group, 
                       marker='o' if show_points else None, markersize=4)
        else:
            # Single series
            x_data = df[chart_data.x_field]
            y_data = df[chart_data.y_field]
            color = colors[0]
            
            if show_area:
                ax.fill_between(x_data, 0, y_data, alpha=0.7, color=color)
            
            line_style = '-' if not smooth else '-'
            ax.plot(x_data, y_data, line_style, color=color,
                   marker='o' if show_points else None, markersize=4)
        
        # Customization
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
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_bar_chart(
        chart_data: ChartData,
        config: ChartConfig,
        horizontal: bool = False,
        stack: bool = False,
        group: bool = False
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a bar chart
        
        Args:
            chart_data: Chart data with category_field, value_field, and optional group_field
            config: Chart configuration
            horizontal: Whether to create horizontal bars
            stack: Whether to stack multiple series
            group: Whether to group multiple series side by side
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        if chart_data.group_field and chart_data.group_field in df.columns:
            # Multiple series
            if stack:
                # Stacked bars
                pivot_df = df.pivot(index=chart_data.category_field, 
                                  columns=chart_data.group_field, 
                                  values=chart_data.value_field).fillna(0)
                if horizontal:
                    pivot_df.plot(kind='barh', stacked=True, ax=ax, color=colors[:len(pivot_df.columns)])
                else:
                    pivot_df.plot(kind='bar', stacked=True, ax=ax, color=colors[:len(pivot_df.columns)])
            elif group:
                # Grouped bars
                pivot_df = df.pivot(index=chart_data.category_field,
                                  columns=chart_data.group_field,
                                  values=chart_data.value_field).fillna(0)
                if horizontal:
                    pivot_df.plot(kind='barh', ax=ax, color=colors[:len(pivot_df.columns)])
                else:
                    pivot_df.plot(kind='bar', ax=ax, color=colors[:len(pivot_df.columns)])
        else:
            # Single series
            categories = df[chart_data.category_field]
            values = df[chart_data.value_field]
            
            if horizontal:
                ax.barh(categories, values, color=colors[0])
            else:
                ax.bar(categories, values, color=colors[0])
        
        # Customization
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
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_pie_chart(
        chart_data: ChartData,
        config: ChartConfig,
        inner_radius: float = 0.0,
        explode_largest: bool = False
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a pie chart
        
        Args:
            chart_data: Chart data with category_field and value_field
            config: Chart configuration
            inner_radius: Inner radius for donut chart (0.0 to 1.0)
            explode_largest: Whether to explode the largest slice
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        categories = df[chart_data.category_field]
        values = df[chart_data.value_field]
        
        # Prepare explode parameter
        explode = None
        if explode_largest:
            max_idx = values.idxmax()
            explode = [0.1 if i == max_idx else 0 for i in range(len(values))]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=categories,
            colors=colors[:len(categories)],
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            wedgeprops=dict(width=1-inner_radius) if inner_radius > 0 else None
        )
        
        # Customization
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_scatter_chart(
        chart_data: ChartData,
        config: ChartConfig,
        size_by_field: bool = False,
        alpha: float = 0.7
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a scatter chart
        
        Args:
            chart_data: Chart data with x_field, y_field, optional group_field and size_field
            config: Chart configuration
            size_by_field: Whether to vary point size by size_field
            alpha: Transparency of points
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        x_data = df[chart_data.x_field]
        y_data = df[chart_data.y_field]
        
        # Determine sizes
        sizes = None
        if size_by_field and chart_data.size_field and chart_data.size_field in df.columns:
            sizes = df[chart_data.size_field] * 20  # Scale for visibility
        else:
            sizes = [50] * len(x_data)  # Default size
        
        if chart_data.group_field and chart_data.group_field in df.columns:
            # Multiple series with different colors
            groups = df[chart_data.group_field].unique()
            for i, group in enumerate(groups):
                group_data = df[df[chart_data.group_field] == group]
                ax.scatter(
                    group_data[chart_data.x_field],
                    group_data[chart_data.y_field],
                    s=sizes if not size_by_field else group_data[chart_data.size_field] * 20,
                    c=colors[i % len(colors)],
                    alpha=alpha,
                    label=group
                )
        else:
            # Single series
            ax.scatter(x_data, y_data, s=sizes, c=colors[0], alpha=alpha)
        
        # Customization
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
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_heatmap(
        chart_data: ChartData,
        config: ChartConfig,
        colormap: str = 'viridis',
        annotate: bool = True
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a heatmap
        
        Args:
            chart_data: Chart data as DataFrame or pivot-ready data
            config: Chart configuration
            colormap: Matplotlib colormap name
            annotate: Whether to show values in cells
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        
        # If data needs to be pivoted
        if all(field in df.columns for field in [chart_data.x_field, chart_data.y_field, chart_data.value_field]):
            pivot_df = df.pivot(index=chart_data.y_field, columns=chart_data.x_field, values=chart_data.value_field)
        else:
            pivot_df = df
        
        # Create heatmap
        sns.heatmap(
            pivot_df,
            annot=annotate,
            cmap=colormap,
            ax=ax,
            cbar_kws={'shrink': 0.8}
        )
        
        # Customization
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title)
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_boxplot(
        chart_data: ChartData,
        config: ChartConfig,
        show_outliers: bool = True
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a box plot
        
        Args:
            chart_data: Chart data with category_field and value_field
            config: Chart configuration
            show_outliers: Whether to show outlier points
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        if chart_data.category_field and chart_data.category_field in df.columns:
            # Grouped box plot
            categories = df[chart_data.category_field].unique()
            data_by_category = [df[df[chart_data.category_field] == cat][chart_data.value_field].dropna() 
                              for cat in categories]
            
            bp = ax.boxplot(data_by_category, labels=categories, showfliers=show_outliers, patch_artist=True)
            
            # Color the boxes
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
        else:
            # Single box plot
            bp = ax.boxplot(df[chart_data.value_field].dropna(), showfliers=show_outliers, patch_artist=True)
            bp['boxes'][0].set_facecolor(colors[0])
            bp['boxes'][0].set_alpha(0.7)
        
        # Customization
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_histogram(
        chart_data: ChartData,
        config: ChartConfig,
        bins: int = 30,
        density: bool = False
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Generate a histogram
        
        Args:
            chart_data: Chart data with value_field
            config: Chart configuration
            bins: Number of bins
            density: Whether to normalize to show density
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        values = df[chart_data.value_field].dropna()
        
        ax.hist(values, bins=bins, density=density, alpha=0.7, color=colors[0], edgecolor='black')
        
        # Customization
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title if config.y_title else ('Density' if density else 'Frequency'))
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_funnel_chart(
        chart_data: ChartData,
        config: ChartConfig,
        sort_descending: bool = True
    ) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """
        Generate a funnel chart
        
        Args:
            chart_data: Chart data with category_field and value_field
            config: Chart configuration
            sort_descending: Whether to sort values in descending order
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        categories = df[chart_data.category_field].tolist()
        values = df[chart_data.value_field].tolist()
        
        # Sort if requested
        if sort_descending:
            sorted_data = sorted(zip(categories, values), key=lambda x: x[1], reverse=True)
            categories, values = zip(*sorted_data)
        
        # Calculate funnel widths (normalized)
        max_value = max(values)
        widths = [v / max_value for v in values]
        
        # Create funnel segments
        y_positions = list(range(len(categories)))
        y_positions.reverse()  # Top to bottom
        
        for i, (category, width) in enumerate(zip(categories, widths)):
            y = y_positions[i]
            color = colors[i % len(colors)]
            
            # Create trapezoid shape
            left = (1 - width) / 2
            right = left + width
            
            # Draw rectangle for each segment
            rect = patches.Rectangle((left, y - 0.4), width, 0.8, 
                                   facecolor=color, alpha=0.7, edgecolor='white', linewidth=2)
            ax.add_patch(rect)
            
            # Add labels
            ax.text(0.5, y, f"{category}\n{values[i]}", 
                   ha='center', va='center', fontweight='bold', color='white')
        
        # Customization
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, len(categories) - 0.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_gauge_chart(
        chart_data: ChartData,
        config: ChartConfig,
        min_value: float = 0,
        max_value: float = 100,
        show_value: bool = True
    ) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """
        Generate a gauge chart
        
        Args:
            chart_data: Chart data with name_field and value_field
            config: Chart configuration
            min_value: Minimum gauge value
            max_value: Maximum gauge value
            show_value: Whether to show the current value
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        # For multiple gauges, arrange them in a grid
        gauges = []
        for _, row in df.iterrows():
            name = row[chart_data.name_field] if chart_data.name_field else "Value"
            value = row[chart_data.value_field]
            gauges.append((name, value))
        
        n_gauges = len(gauges)
        if n_gauges == 1:
            rows, cols = 1, 1
        elif n_gauges <= 4:
            rows, cols = 2, 2
        else:
            rows = int(np.ceil(np.sqrt(n_gauges)))
            cols = int(np.ceil(n_gauges / rows))
        
        fig, axes = plt.subplots(rows, cols, figsize=(config.width/100, config.height/100))
        if n_gauges == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        else:
            axes = axes.flatten()
        
        for i, (name, value) in enumerate(gauges):
            if i >= len(axes):
                break
                
            ax = axes[i]
            color = colors[i % len(colors)]
            
            # Normalize value
            normalized_value = (value - min_value) / (max_value - min_value)
            normalized_value = max(0, min(1, normalized_value))  # Clamp to [0,1]
            
            # Create gauge
            theta = np.linspace(0, np.pi, 100)
            
            # Background arc
            ax.plot(np.cos(theta), np.sin(theta), 'lightgray', linewidth=8)
            
            # Value arc
            value_theta = np.linspace(0, np.pi * normalized_value, int(100 * normalized_value))
            if len(value_theta) > 0:
                ax.plot(np.cos(value_theta), np.sin(value_theta), color, linewidth=8)
            
            # Needle
            needle_angle = np.pi * (1 - normalized_value)  # Reverse for clockwise
            needle_x = 0.8 * np.cos(needle_angle)
            needle_y = 0.8 * np.sin(needle_angle)
            ax.plot([0, needle_x], [0, needle_y], 'black', linewidth=3)
            ax.plot(0, 0, 'ko', markersize=8)
            
            # Labels
            if show_value:
                ax.text(0, -0.3, f"{value:.1f}", ha='center', va='center', 
                       fontsize=12, fontweight='bold')
            ax.text(0, -0.5, name, ha='center', va='center', fontsize=10)
            
            # Scale labels
            for j, scale_value in enumerate([min_value, (min_value + max_value)/2, max_value]):
                angle = np.pi * (1 - j/2)  # 0, π/2, π
                label_x = 1.1 * np.cos(angle)
                label_y = 1.1 * np.sin(angle)
                ax.text(label_x, label_y, f"{scale_value:.0f}", ha='center', va='center', fontsize=8)
            
            ax.set_xlim(-1.3, 1.3)
            ax.set_ylim(-0.7, 1.3)
            ax.set_aspect('equal')
            ax.axis('off')
        
        # Hide unused subplots
        for i in range(n_gauges, len(axes)):
            axes[i].axis('off')
        
        if config.title:
            fig.suptitle(config.title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_radar_chart(
        chart_data: ChartData,
        config: ChartConfig,
        fill_alpha: float = 0.3
    ) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """
        Generate a radar chart
        
        Args:
            chart_data: Chart data with category_field (axes), value_field, and optional group_field
            config: Chart configuration
            fill_alpha: Transparency for filled areas
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100), subplot_kw=dict(projection='polar'))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        # Get unique categories (radar axes)
        categories = df[chart_data.category_field].unique()
        n_vars = len(categories)
        
        # Calculate angles for each axis
        angles = np.linspace(0, 2 * np.pi, n_vars, endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        if chart_data.group_field and chart_data.group_field in df.columns:
            # Multiple series radar
            groups = df[chart_data.group_field].unique()
            
            for i, group in enumerate(groups):
                group_data = df[df[chart_data.group_field] == group]
                
                # Get values for each category
                values = []
                for category in categories:
                    cat_data = group_data[group_data[chart_data.category_field] == category]
                    if not cat_data.empty:
                        values.append(cat_data[chart_data.value_field].iloc[0])
                    else:
                        values.append(0)
                
                values += values[:1]  # Complete the circle
                color = colors[i % len(colors)]
                
                # Plot
                ax.plot(angles, values, 'o-', linewidth=2, label=group, color=color)
                ax.fill(angles, values, alpha=fill_alpha, color=color)
        else:
            # Single series radar
            values = []
            for category in categories:
                cat_data = df[df[chart_data.category_field] == category]
                if not cat_data.empty:
                    values.append(cat_data[chart_data.value_field].iloc[0])
                else:
                    values.append(0)
            
            values += values[:1]  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, color=colors[0])
            ax.fill(angles, values, alpha=fill_alpha, color=colors[0])
        
        # Customize
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, df[chart_data.value_field].max() * 1.1)
        
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold', pad=20)
        
        if config.show_legend and chart_data.group_field:
            ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @staticmethod
    def generate_sankey_chart(
        chart_data: ChartData,
        config: ChartConfig,
        node_width: float = 0.1
    ) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """
        Generate a Sankey diagram
        
        Args:
            chart_data: Chart data with source_field, target_field, and value_field
            config: Chart configuration
            node_width: Width of the nodes
            
        Returns:
            Chart in specified format
        """
        ChartGenerator._setup_theme(config.theme)
        
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        df = ChartGenerator._prepare_data(chart_data)
        colors = ChartGenerator._get_colors(config.theme, config.colors)
        
        # Create Sankey diagram
        sankey = Sankey(ax=ax, scale=0.01, offset=0.2, format='%.0f')
        
        # Prepare data
        sources = df[chart_data.source_field].tolist()
        targets = df[chart_data.target_field].tolist()
        values = df[chart_data.value_field].tolist()
        
        # Get unique nodes
        all_nodes = list(set(sources + targets))
        node_colors = colors[:len(all_nodes)]
        
        # Create flows - simplified version using matplotlib's Sankey
        flows = []
        labels = []
        orientations = []
        
        # Group by source
        source_groups = df.groupby(chart_data.source_field)
        
        for i, (source, group) in enumerate(source_groups):
            group_flows = []
            group_labels = [source]
            group_orientations = [0]  # Source orientation
            
            for _, row in group.iterrows():
                target = row[chart_data.target_field]
                value = row[chart_data.value_field]
                
                group_flows.append(value)  # Outflow
                group_flows.append(-value)  # Inflow to target
                
                group_labels.append(target)
                group_orientations.append(0)  # Source
                group_orientations.append(1)  # Target
            
            # Add to sankey
            sankey.add(flows=group_flows, labels=group_labels, 
                      orientations=group_orientations,
                      facecolor=colors[i % len(colors)], alpha=0.7)
        
        # Finish the diagram
        diagrams = sankey.finish()
        
        # Customization
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        
        ax.axis('off')
        plt.tight_layout()
        result = ChartGenerator._save_chart(fig, config)
        plt.close(fig)
        return result

    @classmethod
    def run(
        cls,
        chart_type: Union[str, ChartType],
        data: Union[List[Dict[str, Any]], pd.DataFrame],
        config: Optional[ChartConfig] = None,
        **kwargs
    ) -> Union[str, bytes, io.BytesIO]:
        """
        Main entry point for chart generation
        
        Args:
            chart_type: Type of chart to generate
            data: Chart data
            config: Chart configuration (uses defaults if not provided)
            **kwargs: Additional arguments specific to chart type
            
        Returns:
            Chart in specified format
            
        Example:
            # Line chart
            result = ChartGenerator.run(
                'line',
                data=[{'time': '2023-01', 'value': 100}, {'time': '2023-02', 'value': 120}],
                config=ChartConfig(title='Sales Trend', x_title='Month', y_title='Sales'),
                x_field='time',
                y_field='value'
            )
            
            # Bar chart with grouping
            result = ChartGenerator.run(
                'bar',
                data=[
                    {'category': 'A', 'value': 100, 'group': 'Q1'},
                    {'category': 'B', 'value': 120, 'group': 'Q1'},
                    {'category': 'A', 'value': 110, 'group': 'Q2'},
                    {'category': 'B', 'value': 130, 'group': 'Q2'}
                ],
                category_field='category',
                value_field='value',
                group_field='group',
                group=True
            )
        """
        if config is None:
            config = ChartConfig()
        
        # Convert string to enum if needed
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type.lower())
        
        # Create ChartData object from kwargs
        chart_data = ChartData(data=data)
        for field in ['x_field', 'y_field', 'category_field', 'value_field', 'group_field', 'size_field']:
            if field in kwargs:
                setattr(chart_data, field, kwargs[field])
        
        # Route to appropriate chart generation method
        try:
            if chart_type == ChartType.LINE:
                return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                    if k in ['smooth', 'show_area', 'show_points', 'stack']})
            
            elif chart_type == ChartType.BAR:
                return cls.generate_bar_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                   if k in ['horizontal', 'stack', 'group']})
            
            elif chart_type == ChartType.PIE:
                return cls.generate_pie_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                   if k in ['inner_radius', 'explode_largest']})
            
            elif chart_type == ChartType.SCATTER:
                return cls.generate_scatter_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                       if k in ['size_by_field', 'alpha']})
            
            elif chart_type == ChartType.HEATMAP:
                return cls.generate_heatmap(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                 if k in ['colormap', 'annotate']})
            
            elif chart_type == ChartType.BOXPLOT:
                return cls.generate_boxplot(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                 if k in ['show_outliers']})
            
            elif chart_type == ChartType.HISTOGRAM:
                return cls.generate_histogram(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                   if k in ['bins', 'density']})
            
            elif chart_type == ChartType.AREA:
                # Area chart is a line chart with show_area=True
                kwargs['show_area'] = True
                return cls.generate_line_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                    if k in ['smooth', 'show_area', 'show_points', 'stack']})
            
            elif chart_type == ChartType.FUNNEL:
                return cls.generate_funnel_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                      if k in ['sort_descending']})
            
            elif chart_type == ChartType.GAUGE:
                return cls.generate_gauge_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                     if k in ['min_value', 'max_value', 'show_value']})
            
            elif chart_type == ChartType.RADAR:
                return cls.generate_radar_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                     if k in ['fill_alpha']})
            
            elif chart_type == ChartType.SANKEY:
                return cls.generate_sankey_chart(chart_data, config, **{k: v for k, v in kwargs.items() 
                                                                      if k in ['node_width']})
            
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
                
        except Exception as e:
            _logger.error(f"Error generating {chart_type.value} chart: {str(e)}")
            raise
    
    @classmethod
    def _get_enhanced_generator(cls):
        """Get enhanced generator instance if available"""
        if cls._enhanced_generator is None:
            try:
                from .enhanced_chart_generator import EnhancedChartGenerator, ChartLimits, ChartPerformanceSettings
                cls._enhanced_generator = EnhancedChartGenerator(
                    limits=ChartLimits(),
                    performance_settings=ChartPerformanceSettings(),
                    enable_caching=True
                )
            except ImportError:
                cls._enhanced_generator = None
        return cls._enhanced_generator

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Get performance statistics (enhanced feature)"""
        try:
            # Try to get from enhanced generator if available
            enhanced = cls._get_enhanced_generator()
            if enhanced:
                return enhanced.get_statistics()
        except:
            pass
        # Return basic stats if enhanced generator not available
        return {
            'charts_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_generation_time': 0.0
        }
    
    @classmethod
    def clear_cache(cls):
        """Clear generation cache (enhanced feature)"""
        try:
            enhanced = cls._get_enhanced_generator()
            if enhanced:
                enhanced.clear_cache()
        except:
            pass  # No cache to clear in basic implementation
