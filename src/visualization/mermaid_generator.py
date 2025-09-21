"""
Mermaid chart generator for converting data to Mermaid syntax.
This enables chart rendering in environments that support Mermaid (like Cursor Chat).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from .chart_config import ChartData, ChartConfig, ChartType

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class MermaidGenerator:
    """
    Generator for converting chart data to Mermaid diagram syntax.
    Supports various chart types that can be represented in Mermaid.
    """

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
    def _sanitize_label(label: str) -> str:
        """Sanitize labels for Mermaid compatibility"""
        if not isinstance(label, str):
            label = str(label)
        # Replace problematic characters
        return label.replace('"', "'").replace('\n', ' ').replace('\r', ' ')

    @staticmethod
    def generate_xychart(chart_data: ChartData, config: ChartConfig, chart_type: str = "line") -> str:
        """Generate Mermaid XY Chart (supports line and bar charts)"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        # Build the Mermaid XY chart
        lines = []
        lines.append("xychart-beta")
        
        if config.title:
            lines.append(f'    title "{MermaidGenerator._sanitize_label(config.title)}"')
        
        # Handle different field mappings
        if chart_data.x_field and chart_data.y_field:
            # Line chart style
            x_values = df[chart_data.x_field].astype(str).tolist()
            y_values = df[chart_data.y_field].tolist()
            
            x_axis_labels = [MermaidGenerator._sanitize_label(x) for x in x_values]
            lines.append(f'    x-axis [{", ".join(x_axis_labels)}]')
            
            y_title = config.y_title or chart_data.y_field or "Values"
            y_min, y_max = min(y_values), max(y_values)
            y_range = y_max - y_min
            y_min_display = max(0, y_min - y_range * 0.1)
            y_max_display = y_max + y_range * 0.1
            lines.append(f'    y-axis "{y_title}" {y_min_display:.0f} --> {y_max_display:.0f}')
            
            if chart_type == "line":
                lines.append(f'    line [{", ".join(map(str, y_values))}]')
            else:  # bar
                lines.append(f'    bar [{", ".join(map(str, y_values))}]')
                
        elif chart_data.category_field and chart_data.value_field:
            # Bar chart style
            categories = df[chart_data.category_field].astype(str).tolist()
            values = df[chart_data.value_field].tolist()
            
            cat_labels = [MermaidGenerator._sanitize_label(cat) for cat in categories]
            lines.append(f'    x-axis [{", ".join(cat_labels)}]')
            
            value_title = config.y_title or chart_data.value_field or "Values"
            v_min, v_max = min(values), max(values)
            v_range = v_max - v_min
            v_min_display = max(0, v_min - v_range * 0.1)
            v_max_display = v_max + v_range * 0.1
            lines.append(f'    y-axis "{value_title}" {v_min_display:.0f} --> {v_max_display:.0f}')
            
            lines.append(f'    bar [{", ".join(map(str, values))}]')
        else:
            raise ValueError("Missing required fields for chart generation")
            
        return '\n'.join(lines)

    @staticmethod
    def generate_pie_chart(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate Mermaid Pie Chart"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        if not (chart_data.category_field and chart_data.value_field):
            raise ValueError("Pie chart requires category_field and value_field")
        
        lines = []
        title = config.title or "Pie Chart"
        lines.append(f'pie title {MermaidGenerator._sanitize_label(title)}')
        
        categories = df[chart_data.category_field].tolist()
        values = df[chart_data.value_field].tolist()
        
        for cat, val in zip(categories, values):
            cat_clean = MermaidGenerator._sanitize_label(str(cat))
            lines.append(f'    "{cat_clean}" : {val}')
        
        return '\n'.join(lines)

    @staticmethod
    def generate_flowchart(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate a flowchart representation of the data"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        lines = []
        lines.append("flowchart TD")
        
        if config.title:
            title_clean = MermaidGenerator._sanitize_label(config.title)
            lines.append(f'    A["{title_clean}"] --> B["Data Visualization"]')
        
        # Create nodes for each data point
        if chart_data.category_field and chart_data.value_field:
            categories = df[chart_data.category_field].tolist()
            values = df[chart_data.value_field].tolist()
            
            lines.append('    B --> C["Categories"]')
            for i, (cat, val) in enumerate(zip(categories[:6], values[:6]), 1):  # Limit to 6 for readability
                cat_clean = MermaidGenerator._sanitize_label(str(cat))
                lines.append(f'    C --> D{i}["{cat_clean}: {val}"]')
                
        elif chart_data.x_field and chart_data.y_field:
            lines.append('    B --> C["Data Points"]')
            x_values = df[chart_data.x_field].tolist()
            y_values = df[chart_data.y_field].tolist()
            
            for i, (x, y) in enumerate(zip(x_values[:6], y_values[:6]), 1):  # Limit to 6
                x_clean = MermaidGenerator._sanitize_label(str(x))
                lines.append(f'    C --> D{i}["{x_clean}: {y}"]')
        
        # Add styling
        lines.append('    style A fill:#e1f5fe')
        lines.append('    style B fill:#f3e5f5')
        lines.append('    style C fill:#e8f5e8')
        
        return '\n'.join(lines)

    @staticmethod
    def generate_gantt_chart(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate a Gantt chart representation (for time-based data)"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        lines = []
        lines.append("gantt")
        
        if config.title:
            lines.append(f'    title {MermaidGenerator._sanitize_label(config.title)}')
        
        lines.append('    dateFormat  YYYY-MM-DD')
        lines.append('    section Data')
        
        # Simple representation - treat categories as tasks
        if chart_data.category_field:
            categories = df[chart_data.category_field].tolist()
            for i, cat in enumerate(categories[:8]):  # Limit for readability
                cat_clean = MermaidGenerator._sanitize_label(str(cat))
                start_date = f'2024-01-{i+1:02d}'
                end_date = f'2024-01-{i+2:02d}'
                lines.append(f'    {cat_clean} : {start_date}, {end_date}')
        
        return '\n'.join(lines)

    @classmethod
    def generate(cls, chart_type: ChartType, chart_data: ChartData, config: ChartConfig, **kwargs) -> str:
        """
        Main entry point for Mermaid generation
        
        Args:
            chart_type: The type of chart to generate
            chart_data: The data to visualize
            config: Chart configuration
            **kwargs: Additional options
            
        Returns:
            Mermaid diagram syntax as string
        """
        try:
            if chart_type == ChartType.LINE:
                return cls.generate_xychart(chart_data, config, "line")
            elif chart_type == ChartType.BAR:
                return cls.generate_xychart(chart_data, config, "bar")
            elif chart_type == ChartType.PIE:
                return cls.generate_pie_chart(chart_data, config)
            elif chart_type == ChartType.AREA:
                # Area charts can be represented as line charts in Mermaid
                return cls.generate_xychart(chart_data, config, "line")
            elif chart_type in [ChartType.SCATTER, ChartType.HISTOGRAM]:
                # Use flowchart representation for complex charts
                return cls.generate_flowchart(chart_data, config)
            else:
                # Fallback to flowchart for unsupported types
                _logger.warning(f"Chart type {chart_type.value} not directly supported in Mermaid, using flowchart representation")
                return cls.generate_flowchart(chart_data, config)
                
        except Exception as e:
            _logger.error(f"Error generating Mermaid chart: {str(e)}")
            # Return a simple error diagram
            return f"""flowchart TD
    A["Chart Generation Error"] --> B["{str(e)}"]
    style A fill:#ffcdd2
    style B fill:#ffcdd2"""
