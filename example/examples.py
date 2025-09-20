# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp.dianomic.com
# FOGLAMP_END

"""
Examples demonstrating the ChartGenerator capabilities

Shows various usage patterns and chart types supported by the ChartGenerator class.
"""

import pandas as pd
from .chart_generator import ChartGenerator
from .chart_config import ChartData, ChartConfig, ChartType, Theme, OutputFormat

__author__ = "Dianomic Systems Inc."
__copyright__ = "Copyright (c) 2025 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def example_line_chart():
    """Example of generating a line chart"""
    # Sample time series data
    data = [
        {'time': '2023-01', 'value': 100, 'series': 'Product A'},
        {'time': '2023-02', 'value': 120, 'series': 'Product A'},
        {'time': '2023-03', 'value': 110, 'series': 'Product A'},
        {'time': '2023-04', 'value': 140, 'series': 'Product A'},
        {'time': '2023-01', 'value': 80, 'series': 'Product B'},
        {'time': '2023-02', 'value': 90, 'series': 'Product B'},
        {'time': '2023-03', 'value': 95, 'series': 'Product B'},
        {'time': '2023-04', 'value': 105, 'series': 'Product B'},
    ]
    
    config = ChartConfig(
        title='Product Sales Trend',
        x_title='Month',
        y_title='Sales ($000)',
        theme=Theme.DEFAULT,
        output_format=OutputFormat.PNG
    )
    
    return ChartGenerator.run(
        ChartType.LINE,
        data,
        config,
        x_field='time',
        y_field='value',
        group_field='series',
        smooth=True,
        show_points=True
    )


def example_bar_chart():
    """Example of generating a grouped bar chart"""
    data = [
        {'category': 'Q1', 'value': 100, 'region': 'North'},
        {'category': 'Q2', 'value': 120, 'region': 'North'},
        {'category': 'Q3', 'value': 110, 'region': 'North'},
        {'category': 'Q4', 'value': 140, 'region': 'North'},
        {'category': 'Q1', 'value': 80, 'region': 'South'},
        {'category': 'Q2', 'value': 90, 'region': 'South'},
        {'category': 'Q3', 'value': 95, 'region': 'South'},
        {'category': 'Q4', 'value': 105, 'region': 'South'},
    ]
    
    config = ChartConfig(
        title='Quarterly Sales by Region',
        x_title='Quarter',
        y_title='Sales ($000)',
        theme=Theme.SEABORN
    )
    
    return ChartGenerator.run(
        ChartType.BAR,
        data,
        config,
        category_field='category',
        value_field='value',
        group_field='region',
        group=True
    )


def example_pie_chart():
    """Example of generating a pie chart"""
    data = [
        {'category': 'Product A', 'value': 35},
        {'category': 'Product B', 'value': 25},
        {'category': 'Product C', 'value': 20},
        {'category': 'Product D', 'value': 15},
        {'category': 'Others', 'value': 5},
    ]
    
    config = ChartConfig(
        title='Market Share Distribution',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.PIE,
        data,
        config,
        category_field='category',
        value_field='value',
        explode_largest=True
    )


def example_scatter_chart():
    """Example of generating a scatter chart"""
    # Generate some sample correlation data
    import numpy as np
    np.random.seed(42)
    
    n_points = 100
    x = np.random.normal(50, 15, n_points)
    y = 2 * x + np.random.normal(0, 10, n_points)
    categories = np.random.choice(['Type A', 'Type B', 'Type C'], n_points)
    sizes = np.random.uniform(10, 50, n_points)
    
    data = [
        {'x': x[i], 'y': y[i], 'category': categories[i], 'size': sizes[i]}
        for i in range(n_points)
    ]
    
    config = ChartConfig(
        title='Correlation Analysis',
        x_title='Feature X',
        y_title='Feature Y',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.SCATTER,
        data,
        config,
        x_field='x',
        y_field='y',
        group_field='category',
        size_field='size',
        size_by_field=True,
        alpha=0.6
    )


def example_heatmap():
    """Example of generating a heatmap"""
    # Create correlation matrix data
    data = []
    variables = ['Temperature', 'Humidity', 'Pressure', 'Wind Speed']
    
    # Simulate correlation matrix
    import numpy as np
    np.random.seed(42)
    correlation_matrix = np.random.rand(4, 4)
    correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2  # Make symmetric
    np.fill_diagonal(correlation_matrix, 1)  # Perfect self-correlation
    
    for i, var1 in enumerate(variables):
        for j, var2 in enumerate(variables):
            data.append({
                'x_var': var1,
                'y_var': var2,
                'correlation': correlation_matrix[i, j]
            })
    
    config = ChartConfig(
        title='Variable Correlation Matrix',
        x_title='Variables',
        y_title='Variables',
        width=600,
        height=600
    )
    
    return ChartGenerator.run(
        ChartType.HEATMAP,
        data,
        config,
        x_field='x_var',
        y_field='y_var',
        value_field='correlation',
        colormap='RdBu_r',
        annotate=True
    )


def example_boxplot():
    """Example of generating a box plot"""
    # Generate sample data with different distributions
    import numpy as np
    np.random.seed(42)
    
    data = []
    categories = ['Group A', 'Group B', 'Group C', 'Group D']
    
    for category in categories:
        if category == 'Group A':
            values = np.random.normal(100, 15, 50)
        elif category == 'Group B':
            values = np.random.normal(120, 20, 50)
        elif category == 'Group C':
            values = np.random.normal(90, 10, 50)
        else:
            values = np.random.normal(110, 25, 50)
        
        for value in values:
            data.append({'category': category, 'value': value})
    
    config = ChartConfig(
        title='Distribution Comparison',
        x_title='Groups',
        y_title='Values',
        theme=Theme.SEABORN
    )
    
    return ChartGenerator.run(
        ChartType.BOXPLOT,
        data,
        config,
        category_field='category',
        value_field='value',
        show_outliers=True
    )


def example_histogram():
    """Example of generating a histogram"""
    # Generate sample normal distribution
    import numpy as np
    np.random.seed(42)
    
    values = np.random.normal(100, 15, 1000)
    data = [{'value': val} for val in values]
    
    config = ChartConfig(
        title='Value Distribution',
        x_title='Value',
        y_title='Frequency',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.HISTOGRAM,
        data,
        config,
        value_field='value',
        bins=30,
        density=False
    )


def example_area_chart():
    """Example of generating an area chart (stacked)"""
    data = [
        {'time': '2023-01', 'value': 100, 'category': 'Category A'},
        {'time': '2023-02', 'value': 120, 'category': 'Category A'},
        {'time': '2023-03', 'value': 110, 'category': 'Category A'},
        {'time': '2023-04', 'value': 140, 'category': 'Category A'},
        {'time': '2023-01', 'value': 80, 'category': 'Category B'},
        {'time': '2023-02', 'value': 90, 'category': 'Category B'},
        {'time': '2023-03', 'value': 95, 'category': 'Category B'},
        {'time': '2023-04', 'value': 105, 'category': 'Category B'},
        {'time': '2023-01', 'value': 60, 'category': 'Category C'},
        {'time': '2023-02', 'value': 70, 'category': 'Category C'},
        {'time': '2023-03', 'value': 75, 'category': 'Category C'},
        {'time': '2023-04', 'value': 85, 'category': 'Category C'},
    ]
    
    config = ChartConfig(
        title='Stacked Area Chart',
        x_title='Time',
        y_title='Values',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.AREA,
        data,
        config,
        x_field='time',
        y_field='value',
        group_field='category',
        stack=True,
        show_area=True
    )


def example_funnel_chart():
    """Example of generating a funnel chart"""
    data = [
        {'category': 'Website Visitors', 'value': 50000},
        {'category': 'Product Views', 'value': 35000},
        {'category': 'Add to Cart', 'value': 15000},
        {'category': 'Checkout Started', 'value': 8000},
        {'category': 'Purchase Completed', 'value': 5000},
    ]
    
    config = ChartConfig(
        title='Sales Conversion Funnel',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.FUNNEL,
        data,
        config,
        category_field='category',
        value_field='value',
        sort_descending=True
    )


def example_gauge_chart():
    """Example of generating gauge charts"""
    data = [
        {'name': 'CPU Usage', 'value': 75.5},
        {'name': 'Memory Usage', 'value': 62.3},
        {'name': 'Disk Usage', 'value': 45.8},
        {'name': 'Network Load', 'value': 89.2},
    ]
    
    config = ChartConfig(
        title='System Performance Dashboard',
        theme=Theme.DARK,
        width=800,
        height=600
    )
    
    return ChartGenerator.run(
        ChartType.GAUGE,
        data,
        config,
        name_field='name',
        value_field='value',
        min_value=0,
        max_value=100,
        show_value=True
    )


def example_radar_chart():
    """Example of generating a radar chart"""
    data = [
        {'category': 'Speed', 'value': 85, 'product': 'Product A'},
        {'category': 'Quality', 'value': 90, 'product': 'Product A'},
        {'category': 'Price', 'value': 70, 'product': 'Product A'},
        {'category': 'Design', 'value': 95, 'product': 'Product A'},
        {'category': 'Support', 'value': 80, 'product': 'Product A'},
        {'category': 'Speed', 'value': 75, 'product': 'Product B'},
        {'category': 'Quality', 'value': 85, 'product': 'Product B'},
        {'category': 'Price', 'value': 90, 'product': 'Product B'},
        {'category': 'Design', 'value': 70, 'product': 'Product B'},
        {'category': 'Support', 'value': 95, 'product': 'Product B'},
    ]
    
    config = ChartConfig(
        title='Product Comparison Radar',
        theme=Theme.DEFAULT
    )
    
    return ChartGenerator.run(
        ChartType.RADAR,
        data,
        config,
        category_field='category',
        value_field='value',
        group_field='product',
        fill_alpha=0.3
    )


def example_sankey_chart():
    """Example of generating a Sankey diagram"""
    data = [
        {'source': 'Coal', 'target': 'Electricity', 'value': 40},
        {'source': 'Natural Gas', 'target': 'Electricity', 'value': 30},
        {'source': 'Solar', 'target': 'Electricity', 'value': 20},
        {'source': 'Wind', 'target': 'Electricity', 'value': 10},
        {'source': 'Electricity', 'target': 'Residential', 'value': 35},
        {'source': 'Electricity', 'target': 'Commercial', 'value': 40},
        {'source': 'Electricity', 'target': 'Industrial', 'value': 25},
    ]
    
    config = ChartConfig(
        title='Energy Flow Diagram',
        theme=Theme.DEFAULT,
        width=1000,
        height=600
    )
    
    return ChartGenerator.run(
        ChartType.SANKEY,
        data,
        config,
        source_field='source',
        target_field='target',
        value_field='value'
    )


if __name__ == "__main__":
    """Run examples and save to files"""
    import os
    
    # Create output directory
    output_dir = "chart_examples"
    os.makedirs(output_dir, exist_ok=True)
    
    examples = [
        ("line_chart", example_line_chart),
        ("bar_chart", example_bar_chart),
        ("pie_chart", example_pie_chart),
        ("scatter_chart", example_scatter_chart),
        ("heatmap", example_heatmap),
        ("boxplot", example_boxplot),
        ("histogram", example_histogram),
        ("area_chart", example_area_chart),
        ("funnel_chart", example_funnel_chart),
        ("gauge_chart", example_gauge_chart),
        ("radar_chart", example_radar_chart),
        ("sankey_chart", example_sankey_chart),
    ]
    
    for name, example_func in examples:
        try:
            print(f"Generating {name}...")
            result = example_func()
            
            # Save to file
            output_path = os.path.join(output_dir, f"{name}.png")
            with open(output_path, 'wb') as f:
                f.write(result)
            
            print(f"Saved {name} to {output_path}")
            
        except Exception as e:
            print(f"Error generating {name}: {str(e)}")
    
    print("Examples generation completed!")
