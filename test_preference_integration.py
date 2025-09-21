#!/usr/bin/env python3
"""
Test to verify that user preferences are properly integrated with render_chart.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock
import json

def test_preference_integration():
    """Test that configure_preferences settings are used in render_chart."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("🧪 Testing Preference Integration with render_chart")
    print("=" * 50)
    
    configure_func = registered_tools.get('configure_preferences')
    render_func = registered_tools.get('render_chart')
    
    # Clean up any existing config file
    config_file = os.path.expanduser("~/.plots_mcp_config.json")
    if os.path.exists(config_file):
        os.remove(config_file)
    
    # Step 1: Set user preferences
    print("\n1️⃣ Setting user preferences...")
    config_result = configure_func(
        output_format="mcp_image",
        theme="dark", 
        chart_width=1000,
        chart_height=800
    )
    
    print(f"   Config result: {config_result.get('status', 'unknown')}")
    
    # Verify config file was created
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        print(f"   ✅ Config saved: {saved_config}")
    else:
        print("   ❌ Config file not created!")
        return
    
    # Step 2: Test that render_chart uses these preferences
    print("\n2️⃣ Testing render_chart with preferences...")
    
    test_data = [
        {"category": "A", "value": 10},
        {"category": "B", "value": 20},
        {"category": "C", "value": 15}
    ]
    
    # Call render_chart WITHOUT specifying output_format, theme, width, height
    # It should use the user preferences we just set
    result = render_func(
        chart_type="bar",
        data=test_data,
        field_map={"category_field": "category", "value_field": "value"}
        # NOTE: No output_format, theme, width, height specified - should use preferences
    )
    
    print(f"   Render result status: {result.get('status', 'unknown')}")
    
    # Step 3: Analyze if preferences were applied
    print("\n3️⃣ Analyzing preference application...")
    
    success = True
    issues = []
    
    # Check output format
    if result.get("status") == "success":
        content = result.get("content", [])
        if content and len(content) > 0:
            content_type = content[0].get("type", "")
            if content_type == "image":
                print("   ✅ Output format: mcp_image (matches preference)")
            elif content_type == "text":
                print("   ❌ Output format: mcp_text (should be mcp_image)")
                issues.append("Output format not applied")
                success = False
            else:
                print(f"   ❌ Unknown output format: {content_type}")
                issues.append("Unknown output format")
                success = False
        else:
            print("   ❌ No content in result")
            issues.append("No content generated")
            success = False
    else:
        print(f"   ❌ Chart generation failed: {result.get('error', 'unknown error')}")
        issues.append("Chart generation failed")
        success = False
    
    # Step 4: Test preference override
    print("\n4️⃣ Testing preference override...")
    
    override_result = render_func(
        chart_type="bar",
        data=test_data,
        field_map={"category_field": "category", "value_field": "value"},
        output_format="mermaid"  # This should override the preference
    )
    
    if override_result.get("status") == "success":
        override_content = override_result.get("content", [])
        if override_content and override_content[0].get("type") == "text":
            print("   ✅ Override works: mermaid output generated")
        else:
            print("   ❌ Override failed: should be text/mermaid")
            issues.append("Override not working")
            success = False
    else:
        print("   ❌ Override test failed")
        issues.append("Override test failed")
        success = False
    
    # Final results
    print("\n" + "=" * 50)
    if success:
        print("🎉 All preference integration tests passed!")
    else:
        print("❌ Preference integration has issues:")
        for issue in issues:
            print(f"   • {issue}")
    
    # Clean up
    if os.path.exists(config_file):
        os.remove(config_file)

if __name__ == "__main__":
    test_preference_integration()
