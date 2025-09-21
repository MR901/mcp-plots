#!/usr/bin/env python3
"""
Test script to reproduce the None error.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock

def test_none_error():
    """Test various scenarios that might cause None errors."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("🧪 Testing scenarios that might cause None errors")
    print("=" * 50)
    
    render_func = registered_tools.get('render_chart')
    
    # Test cases that might cause None errors
    test_cases = [
        {
            "name": "Sankey without proper fields",
            "chart_type": "sankey",
            "data": [{"source": "A", "target": "X", "value": 10}],
            "field_map": {}  # Missing field mappings
        },
        {
            "name": "Sankey with missing value field",
            "chart_type": "sankey", 
            "data": [{"source": "A", "target": "X"}],  # No value field
            "field_map": {"source_field": "source", "target_field": "target"}
        },
        {
            "name": "Sankey with None fields",
            "chart_type": "sankey",
            "data": [{"source": "A", "target": "X", "value": 10}],
            "field_map": {"source_field": None, "target_field": "target", "value_field": "value"}
        },
        {
            "name": "Empty data",
            "chart_type": "bar",
            "data": [],
            "field_map": {"category_field": "cat", "value_field": "val"}
        },
        {
            "name": "Invalid chart type",
            "chart_type": "unknown_type",
            "data": [{"cat": "A", "val": 10}],
            "field_map": {"category_field": "cat", "value_field": "val"}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        try:
            result = render_func(
                chart_type=test_case["chart_type"],
                data=test_case["data"],
                field_map=test_case["field_map"]
            )
            
            if isinstance(result, dict):
                if "status" in result and result["status"] == "error":
                    error_msg = result.get("error", "Unknown error")
                    print(f"   ❌ ERROR: {error_msg}")
                    if str(error_msg) == "None":
                        print(f"   🎯 FOUND IT! This case produces 'None' error")
                elif "content" in result:
                    print(f"   ✅ SUCCESS: Generated content")
                else:
                    print(f"   ⚠️  UNEXPECTED: {result}")
            else:
                print(f"   ⚠️  UNEXPECTED TYPE: {type(result)} - {result}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
            if str(e) == "None":
                print(f"   🎯 FOUND IT! This case produces 'None' exception")
    
    print("\n" + "=" * 50)
    print("✅ None error test completed!")

if __name__ == "__main__":
    test_none_error()
