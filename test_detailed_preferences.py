#!/usr/bin/env python3
"""
Detailed test to check if ALL user preferences are being applied.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock
import json

def test_detailed_preferences():
    """Test that ALL configure_preferences settings are used in render_chart."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("🔍 Detailed Preference Application Test")
    print("=" * 40)
    
    configure_func = registered_tools.get('configure_preferences')
    render_func = registered_tools.get('render_chart')
    
    # Clean up any existing config file
    config_file = os.path.expanduser("~/.plots_mcp_config.json")
    if os.path.exists(config_file):
        os.remove(config_file)
    
    # Set specific preferences
    print("\n1️⃣ Setting detailed preferences...")
    configure_func(
        output_format="mcp_text",  # Should generate SVG
        theme="seaborn",           # Should use seaborn theme
        chart_width=1200,          # Should set width to 1200
        chart_height=900           # Should set height to 900
    )
    
    # Verify saved preferences
    with open(config_file, 'r') as f:
        saved_config = json.load(f)
    
    user_prefs = saved_config['user_preferences']
    print(f"   Saved preferences: {user_prefs}")
    
    # Test with a chart that should use these preferences
    print("\n2️⃣ Rendering chart with preferences...")
    
    test_data = [
        {"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 15}
    ]
    
    result = render_func(
        chart_type="line",
        data=test_data,
        field_map={"x_field": "x", "y_field": "y"}
    )
    
    print(f"   Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        content = result.get('content', [])
        if content:
            content_type = content[0].get('type')
            print(f"   Content type: {content_type}")
            
            if content_type == 'text':
                # This should be SVG content
                svg_content = content[0].get('text', '')
                print(f"   SVG length: {len(svg_content)} characters")
                
                # Check if dimensions are in SVG
                if 'width="1200"' in svg_content and 'height="900"' in svg_content:
                    print("   ✅ Custom dimensions applied!")
                else:
                    print("   ❌ Custom dimensions NOT found in SVG")
                    print(f"   SVG preview: {svg_content[:200]}...")
            else:
                print(f"   ❌ Expected text/SVG but got {content_type}")
    
    # Test 3: Direct inspection of ChartConfig creation
    print("\n3️⃣ Testing ChartConfig creation directly...")
    
    # Let's monkey-patch to inspect the ChartConfig being created
    from src.visualization.chart_config import ChartConfig
    original_init = ChartConfig.__init__
    captured_config = {}
    
    def capture_init(self, **kwargs):
        captured_config.update(kwargs)
        return original_init(self, **kwargs)
    
    ChartConfig.__init__ = capture_init
    
    # Render again to capture the config
    render_func(
        chart_type="bar",
        data=[{"cat": "A", "val": 10}],
        field_map={"category_field": "cat", "value_field": "val"}
    )
    
    # Restore original init
    ChartConfig.__init__ = original_init
    
    print(f"   Captured ChartConfig parameters:")
    for key, value in captured_config.items():
        print(f"     {key}: {value}")
    
    # Check if our preferences were applied
    expected_checks = {
        "width": 1200,
        "height": 900,
        "theme": "seaborn"  # This might be a Theme enum
    }
    
    print("\n4️⃣ Preference application analysis:")
    for key, expected_value in expected_checks.items():
        actual_value = captured_config.get(key)
        if key == "theme":
            # Handle theme enum
            if hasattr(actual_value, 'value'):
                actual_value = actual_value.value
        
        if actual_value == expected_value:
            print(f"   ✅ {key}: {actual_value} (matches preference)")
        else:
            print(f"   ❌ {key}: {actual_value} (expected {expected_value})")
    
    # Clean up
    if os.path.exists(config_file):
        os.remove(config_file)

if __name__ == "__main__":
    test_detailed_preferences()
