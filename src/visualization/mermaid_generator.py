"""
Mermaid chart generator for converting data to Mermaid syntax.
This enables chart rendering in environments that support Mermaid (like Cursor Chat).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from .chart_config import ChartData, ChartConfig, ChartType
from .field_validator import FieldValidator

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
            # Fields are already validated by FieldValidator
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
            # Fields are already validated by FieldValidator
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
        
        # Fields are already validated by FieldValidator
        
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

    @staticmethod
    def generate_histogram_mermaid(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate histogram as bar chart in Mermaid"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        # Fields are already validated by FieldValidator
        values = df[chart_data.value_field]
        bins = 10  # Simple binning
        min_val, max_val = values.min(), values.max()
        bin_width = (max_val - min_val) / bins
        
        bin_counts = {}
        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width
            bin_label = f"{bin_start:.1f}-{bin_end:.1f}"
            count = len(values[(values >= bin_start) & (values < bin_end)])
            if i == bins - 1:  # Include max value in last bin
                count = len(values[(values >= bin_start) & (values <= bin_end)])
            bin_counts[bin_label] = count
        
        title = config.title or "Histogram"
        
        lines = [f'xychart-beta']
        lines.append(f'    title "{title}"')
        x_axis_labels = ", ".join(f'"{k}"' for k in bin_counts.keys())
        lines.append(f'    x-axis [{x_axis_labels}]')
        lines.append(f'    y-axis "Frequency" 0 --> {max(bin_counts.values())}')
        lines.append(f'    bar [{", ".join(str(v) for v in bin_counts.values())}]')
        
        return '\n'.join(lines)

    @staticmethod
    def generate_funnel_mermaid(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate funnel chart using flowchart"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        # Fields are already validated by FieldValidator
        df_sorted = df.sort_values(chart_data.value_field, ascending=False)
        
        title = config.title or "Funnel Chart"
        
        lines = [f'flowchart TD']
        if title:
            lines.append(f'    Title["{title}"]')
        
        # Create funnel stages
        prev_node = "Title" if title else None
        
        for i, (_, row) in enumerate(df_sorted.iterrows()):
            category = MermaidGenerator._sanitize_label(str(row[chart_data.category_field]))
            value = row[chart_data.value_field]
            
            node_id = f"Stage{i}"
            node_label = f"{category}: {value}"
            
            # Use different shapes for visual funnel effect
            if i == 0:
                shape = f'{node_id}["{node_label}"]'
            elif i == len(df_sorted) - 1:
                shape = f'{node_id}("{node_label}")'
            else:
                shape = f'{node_id}["{node_label}"]'
            
            lines.append(f'    {shape}')
            
            if prev_node:
                lines.append(f'    {prev_node} --> {node_id}')
            
            prev_node = node_id
        
        # Add styling for funnel effect
        for i in range(len(df_sorted)):
            node_id = f"Stage{i}"
            # Gradient from green to red
            if i < len(df_sorted) / 3:
                color = "#90EE90"  # Light green
            elif i < 2 * len(df_sorted) / 3:
                color = "#FFD700"  # Gold
            else:
                color = "#FFB6C1"  # Light pink
            
            lines.append(f'    style {node_id} fill:{color}')
        
        return '\n'.join(lines)

    @staticmethod
    def generate_gauge_mermaid(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate gauge chart representation"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        # Fields are already validated by FieldValidator
        value = df[chart_data.value_field].iloc[0]  # Take first value
        title = config.title or "Gauge"
        
        # Create a simple gauge representation using flowchart
        lines = [f'flowchart LR']
        lines.append(f'    A["📊 {title}"]')
        lines.append(f'    B["{value}"]')
        lines.append(f'    A --> B')
        
        # Color based on value (assuming 0-100 scale)
        if value < 30:
            color = "#ffcdd2"  # Red
        elif value < 70:
            color = "#fff3cd"  # Yellow
        else:
            color = "#d4edda"  # Green
        
        lines.append(f'    style B fill:{color}')
        
        return '\n'.join(lines)

    @staticmethod
    def generate_sankey_mermaid(chart_data: ChartData, config: ChartConfig) -> str:
        """Generate Sankey diagram using flowchart"""
        df = MermaidGenerator._prepare_data(chart_data)
        
        # Fields are already validated by FieldValidator
        
        title = config.title or "Flow Diagram"
        
        lines = [f'flowchart LR']
        if title:
            lines.append(f'    Title["{title}"]')
        
        # Create nodes and connections
        sources = df[chart_data.source_field].unique()
        targets = df[chart_data.target_field].unique()
        
        # Add source nodes
        for source in sources:
            source_id = f"S_{MermaidGenerator._sanitize_label(str(source)).replace(' ', '_')}"
            lines.append(f'    {source_id}["{source}"]')
        
        # Add target nodes  
        for target in targets:
            target_id = f"T_{MermaidGenerator._sanitize_label(str(target)).replace(' ', '_')}"
            lines.append(f'    {target_id}["{target}"]')
        
        # Add flows
        for _, row in df.iterrows():
            source = str(row[chart_data.source_field])
            target = str(row[chart_data.target_field])  
            
            # Handle value field safely
            if chart_data.value_field and chart_data.value_field in df.columns:
                value = row[chart_data.value_field]
                # Use thick arrows for larger values
                mean_value = df[chart_data.value_field].mean()
                arrow = "==>" if value > mean_value else "-->"
            else:
                value = 1
                arrow = "-->"
            
            source_id = f"S_{MermaidGenerator._sanitize_label(source).replace(' ', '_')}"
            target_id = f"T_{MermaidGenerator._sanitize_label(target).replace(' ', '_')}"
            
            lines.append(f'    {source_id} {arrow} {target_id}')
            lines.append(f'    {source_id} -.->|{value}| {target_id}')
        
        # Style source and target nodes differently
        for source in sources:
            source_id = f"S_{MermaidGenerator._sanitize_label(str(source)).replace(' ', '_')}"
            lines.append(f'    style {source_id} fill:#e1f5fe')
        
        for target in targets:
            target_id = f"T_{MermaidGenerator._sanitize_label(str(target)).replace(' ', '_')}"
            lines.append(f'    style {target_id} fill:#f3e5f5')
        
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
            elif chart_type == ChartType.SCATTER:
                # Represent scatter plot as xychart
                return cls.generate_xychart(chart_data, config, "line")
            elif chart_type == ChartType.HISTOGRAM:
                # Represent histogram as bar chart
                return cls.generate_histogram_mermaid(chart_data, config)
            elif chart_type == ChartType.FUNNEL:
                # Create a visual funnel using flowchart
                return cls.generate_funnel_mermaid(chart_data, config)
            elif chart_type == ChartType.GAUGE:
                # Create a gauge representation using flowchart
                return cls.generate_gauge_mermaid(chart_data, config)
            elif chart_type == ChartType.SANKEY:
                # Create a sankey diagram using flowchart
                return cls.generate_sankey_mermaid(chart_data, config)
            elif chart_type in [ChartType.BOXPLOT, ChartType.HEATMAP, ChartType.RADAR]:
                # Use flowchart representation for complex statistical charts
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
