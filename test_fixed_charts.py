#!/usr/bin/env python3
"""
Test script to verify the fixes work and charts generate correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock

def test_fixed_charts():
    """Test that the fixes work and charts generate correctly."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("🧪 Testing Fixed Chart Generation")
    print("=" * 40)
    
    render_func = registered_tools.get('render_chart')
    
    # Test cases that should work now
    test_cases = [
        {
            "name": "Valid Sankey chart",
            "chart_type": "sankey",
            "data": [
                {"source": "A", "target": "X", "value": 10},
                {"source": "B", "target": "Y", "value": 20},
                {"source": "A", "target": "Y", "value": 5}
            ],
            "field_map": {"source_field": "source", "target_field": "target", "value_field": "value"}
        },
        {
            "name": "Valid Funnel chart",
            "chart_type": "funnel",
            "data": [
                {"stage": "Awareness", "value": 1000},
                {"stage": "Interest", "value": 500},
                {"stage": "Purchase", "value": 100}
            ],
            "field_map": {"category_field": "stage", "value_field": "value"}
        },
        {
            "name": "Valid Gauge chart",
            "chart_type": "gauge",
            "data": [{"metric": "Performance", "value": 85}],
            "field_map": {"value_field": "value"}
        },
        {
            "name": "Valid Bar chart",
            "chart_type": "bar",
            "data": [
                {"category": "A", "value": 10},
                {"category": "B", "value": 20},
                {"category": "C", "value": 15}
            ],
            "field_map": {"category_field": "category", "value_field": "value"}
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
                if "content" in result:
                    content = result["content"][0]
                    if content.get("type") == "text":
                        mermaid_text = content.get("text", "")
                        first_line = mermaid_text.split('\n')[0]
                        print(f"   ✅ SUCCESS: {first_line}")
                    else:
                        print(f"   ✅ SUCCESS: Generated {content.get('type')} content")
                elif "status" in result and result["status"] == "error":
                    print(f"   ❌ ERROR: {result['error']}")
                else:
                    print(f"   ⚠️  UNEXPECTED: {result}")
            else:
                print(f"   ⚠️  UNEXPECTED TYPE: {type(result)}")
                
        except Exception as e:
            print(f"   💥 EXCEPTION: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Fixed chart test completed!")

if __name__ == "__main__":
    test_fixed_charts()
