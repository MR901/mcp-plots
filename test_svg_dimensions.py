#!/usr/bin/env python3
"""
Test to verify SVG dimensions are correctly applied.
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock
import json

def test_svg_dimensions():
    """Test that custom dimensions appear in SVG output."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("📐 Testing SVG Dimension Application")
    print("=" * 40)
    
    configure_func = registered_tools.get('configure_preferences')
    render_func = registered_tools.get('render_chart')
    
    # Clean up any existing config file
    config_file = os.path.expanduser("~/.plots_mcp_config.json")
    if os.path.exists(config_file):
        os.remove(config_file)
    
    # Set custom dimensions
    print("\n1️⃣ Setting custom dimensions...")
    configure_func(
        output_format="mcp_text",  # SVG output
        chart_width=1000,          # 1000px width
        chart_height=750           # 750px height
    )
    
    # Generate chart
    test_data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
    
    result = render_func(
        chart_type="line",
        data=test_data,
        field_map={"x_field": "x", "y_field": "y"}
    )
    
    if result.get('status') == 'success':
        content = result.get('content', [])
        if content and content[0].get('type') == 'text':
            svg_content = content[0].get('text', '')
            
            print(f"\n2️⃣ Analyzing SVG content...")
            print(f"   SVG length: {len(svg_content)} characters")
            
            # Extract SVG dimensions using regex
            width_match = re.search(r'width="([^"]+)"', svg_content)
            height_match = re.search(r'height="([^"]+)"', svg_content)
            viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
            
            print(f"   Width attribute: {width_match.group(1) if width_match else 'Not found'}")
            print(f"   Height attribute: {height_match.group(1) if height_match else 'Not found'}")
            print(f"   ViewBox attribute: {viewbox_match.group(1) if viewbox_match else 'Not found'}")
            
            # Show first few lines of SVG for inspection
            svg_lines = svg_content.split('\n')[:10]
            print(f"\n3️⃣ SVG header:")
            for i, line in enumerate(svg_lines):
                print(f"   {i+1}: {line}")
            
            # Check if matplotlib figsize was applied correctly
            # figsize=(10.0, 7.5) should result in 10*100=1000px, 7.5*100=750px
            expected_figsize_width = 1000 / 100  # 10.0 inches
            expected_figsize_height = 750 / 100  # 7.5 inches
            
            print(f"\n4️⃣ Expected matplotlib figsize:")
            print(f"   Width: {expected_figsize_width} inches")
            print(f"   Height: {expected_figsize_height} inches")
            
            # Matplotlib's SVG output might use points (72 DPI) or inches
            # 10 inches * 72 points/inch = 720 points
            expected_points_width = expected_figsize_width * 72
            expected_points_height = expected_figsize_height * 72
            
            print(f"\n5️⃣ Expected SVG dimensions (if using 72 DPI):")
            print(f"   Width: {expected_points_width} points")
            print(f"   Height: {expected_points_height} points")
            
        else:
            print("   ❌ No SVG content found")
    else:
        print(f"   ❌ Chart generation failed: {result.get('error')}")
    
    # Clean up
    if os.path.exists(config_file):
        os.remove(config_file)

if __name__ == "__main__":
    test_svg_dimensions()
