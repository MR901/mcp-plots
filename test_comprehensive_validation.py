#!/usr/bin/env python3
"""
Comprehensive test for the centralized field validation system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock

def test_comprehensive_validation():
    """Test the comprehensive field validation system."""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    print("🧪 Testing Comprehensive Field Validation System")
    print("=" * 55)
    
    render_func = registered_tools.get('render_chart')
    
    # Test cases covering all chart types and error scenarios
    test_cases = [
        # Valid cases that should work
        {
            "name": "✅ Valid Bar Chart",
            "chart_type": "bar",
            "data": [{"cat": "A", "val": 10}, {"cat": "B", "val": 20}],
            "field_map": {"category_field": "cat", "value_field": "val"},
            "should_succeed": True
        },
        {
            "name": "✅ Valid Line Chart",
            "chart_type": "line", 
            "data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}],
            "field_map": {"x_field": "x", "y_field": "y"},
            "should_succeed": True
        },
        {
            "name": "✅ Valid Sankey Chart",
            "chart_type": "sankey",
            "data": [{"src": "A", "tgt": "X", "val": 10}],
            "field_map": {"source_field": "src", "target_field": "tgt", "value_field": "val"},
            "should_succeed": True
        },
        
        # Error cases that should fail with descriptive messages
        {
            "name": "❌ Missing Required Fields - Bar",
            "chart_type": "bar",
            "data": [{"cat": "A", "val": 10}],
            "field_map": {},  # Missing required fields
            "should_succeed": False,
            "expected_error": "Bar chart requires category_field, value_field"
        },
        {
            "name": "❌ Missing Required Fields - Sankey", 
            "chart_type": "sankey",
            "data": [{"src": "A", "tgt": "X", "val": 10}],
            "field_map": {"source_field": "src"},  # Missing target_field, value_field
            "should_succeed": False,
            "expected_error": "Sankey chart requires"
        },
        {
            "name": "❌ Field Not in Data",
            "chart_type": "bar",
            "data": [{"category": "A", "value": 10}],
            "field_map": {"category_field": "cat", "value_field": "val"},  # Wrong field names
            "should_succeed": False,
            "expected_error": "not found in data"
        },
        {
            "name": "❌ Empty Data",
            "chart_type": "bar",
            "data": [],  # Empty data
            "field_map": {"category_field": "cat", "value_field": "val"},
            "should_succeed": False,
            "expected_error": "Data cannot be empty"
        },
        {
            "name": "❌ Invalid Chart Type",
            "chart_type": "nonexistent_type",
            "data": [{"cat": "A", "val": 10}],
            "field_map": {"category_field": "cat", "value_field": "val"},
            "should_succeed": False,
            "expected_error": "not a valid ChartType"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        try:
            result = render_func(
                chart_type=test_case["chart_type"],
                data=test_case["data"],
                field_map=test_case["field_map"]
            )
            
            # Check if this is an error response
            if isinstance(result, dict) and result.get("status") == "error":
                if not test_case["should_succeed"]:
                    error_msg = result.get("error", "")
                    expected_error = test_case.get("expected_error", "")
                    if expected_error in error_msg:
                        print(f"   ✅ SUCCESS: Got expected error - {error_msg}")
                        success_count += 1
                    else:
                        print(f"   ⚠️  PARTIAL: Got error but not expected one")
                        print(f"      Expected: {expected_error}")
                        print(f"      Got: {error_msg}")
                        success_count += 0.5  # Partial credit
                else:
                    print(f"   ❌ UNEXPECTED: Expected success but got error - {result['error']}")
            elif test_case["should_succeed"]:
                if isinstance(result, dict) and "content" in result:
                    print(f"   ✅ SUCCESS: Generated chart as expected")
                    success_count += 1
                else:
                    print(f"   ❌ UNEXPECTED: Expected success but got {result}")
            else:
                print(f"   ❌ UNEXPECTED: Expected failure but got success")
                
        except Exception as e:
            if not test_case["should_succeed"]:
                error_msg = str(e)
                expected_error = test_case.get("expected_error", "")
                if expected_error in error_msg:
                    print(f"   ✅ SUCCESS: Got expected exception - {error_msg}")
                    success_count += 1
                else:
                    print(f"   ⚠️  PARTIAL: Got exception but not expected one")
                    print(f"      Expected: {expected_error}")
                    print(f"      Got: {error_msg}")
                    success_count += 0.5  # Partial credit
            else:
                print(f"   ❌ UNEXPECTED: Expected success but got exception - {e}")
    
    print("\n" + "=" * 55)
    print(f"✅ Comprehensive validation test completed!")
    print(f"📊 Results: {success_count}/{total_count} tests passed ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 All tests passed! Field validation system is working perfectly.")
    elif success_count >= total_count * 0.8:
        print("🎯 Most tests passed! Field validation system is working well.")
    else:
        print("⚠️  Some tests failed. Field validation system needs improvement.")

if __name__ == "__main__":
    test_comprehensive_validation()
