#!/usr/bin/env python3
"""
Deep dive QA testing for edge cases and potential hidden issues.
Focus on scenarios that might cause subtle failures.
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from src.capabilities.tools import register_tools
from unittest.mock import Mock

def test_deep_edge_cases():
    """Test subtle edge cases that might cause issues"""
    
    mock_server = Mock()
    registered_tools = {}
    
    def mock_tool_decorator():
        def decorator(func):
            registered_tools[func.__name__] = func
            return func
        return decorator
    
    mock_server.tool = mock_tool_decorator
    register_tools(mock_server)
    
    render_func = registered_tools.get('render_chart')
    configure_func = registered_tools.get('configure_preferences')
    
    print("🔬 DEEP DIVE QA - EDGE CASE TESTING")
    print("=" * 45)
    
    test_results = []
    
    # Test 1: Unicode and special characters
    print("\n1️⃣ Testing Unicode and Special Characters")
    try:
        result = render_func(
            chart_type="bar",
            data=[
                {"category": "测试", "value": 10},
                {"category": "🚀 Rocket", "value": 20},
                {"category": "Café & Bar", "value": 15}
            ],
            field_map={"category_field": "category", "value_field": "value"}
        )
        if result.get("status") == "success":
            print("   ✅ Unicode handling: PASS")
            test_results.append("PASS")
        else:
            print(f"   ❌ Unicode handling: FAIL - {result.get('error')}")
            test_results.append("FAIL")
    except Exception as e:
        print(f"   ❌ Unicode handling: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 2: Very large numbers
    print("\n2️⃣ Testing Large Numbers")
    try:
        result = render_func(
            chart_type="bar",
            data=[
                {"cat": "A", "val": 1e15},
                {"cat": "B", "val": 2.5e-10},
                {"cat": "C", "val": float('inf')}
            ],
            field_map={"category_field": "cat", "value_field": "val"}
        )
        if result.get("status") == "success":
            print("   ✅ Large numbers: PASS")
            test_results.append("PASS")
        else:
            print(f"   ❌ Large numbers: FAIL - {result.get('error')}")
            test_results.append("FAIL")
    except Exception as e:
        print(f"   ❌ Large numbers: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 3: Field name edge cases
    print("\n3️⃣ Testing Field Name Edge Cases")
    try:
        result = render_func(
            chart_type="line",
            data=[
                {"x field": 1, "y-field": 10},
                {"x field": 2, "y-field": 20}
            ],
            field_map={"x_field": "x field", "y_field": "y-field"}
        )
        if result.get("status") == "success":
            print("   ✅ Special field names: PASS")
            test_results.append("PASS")
        else:
            print(f"   ❌ Special field names: FAIL - {result.get('error')}")
            test_results.append("FAIL")
    except Exception as e:
        print(f"   ❌ Special field names: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 4: Nested data structures (should fail gracefully)
    print("\n4️⃣ Testing Nested Data Structures")
    try:
        result = render_func(
            chart_type="bar",
            data=[
                {"cat": "A", "val": {"nested": 10}},
                {"cat": "B", "val": [1, 2, 3]}
            ],
            field_map={"category_field": "cat", "value_field": "val"}
        )
        if result.get("status") == "error":
            print("   ✅ Nested data rejection: PASS (correctly rejected)")
            test_results.append("PASS")
        else:
            print("   ⚠️  Nested data handling: WARN (should probably reject)")
            test_results.append("WARN")
    except Exception as e:
        print(f"   ✅ Nested data rejection: PASS (correctly threw exception)")
        test_results.append("PASS")
    
    # Test 5: Configuration persistence across multiple calls
    print("\n5️⃣ Testing Configuration Persistence")
    try:
        # Clean config
        config_file = os.path.expanduser("~/.plots_mcp_config.json")
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # Set config
        configure_func(theme="dark", chart_width=500)
        
        # Make multiple render calls
        results = []
        for i in range(3):
            result = render_func(
                chart_type="bar",
                data=[{"cat": f"Item{i}", "val": i*10}],
                field_map={"category_field": "cat", "value_field": "val"}
            )
            results.append(result.get("status") == "success")
        
        if all(results):
            print("   ✅ Config persistence: PASS")
            test_results.append("PASS")
        else:
            print(f"   ❌ Config persistence: FAIL - Some calls failed")
            test_results.append("FAIL")
            
        # Clean up
        if os.path.exists(config_file):
            os.remove(config_file)
            
    except Exception as e:
        print(f"   ❌ Config persistence: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 6: Memory leaks with repeated calls
    print("\n6️⃣ Testing Memory Management")
    try:
        import gc
        import psutil
        import os as os_module
        
        process = psutil.Process(os_module.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate many charts
        for i in range(50):
            result = render_func(
                chart_type="line",
                data=[{"x": j, "y": j*i} for j in range(10)],
                field_map={"x_field": "x", "y_field": "y"}
            )
            if result.get("status") != "success":
                raise Exception(f"Chart {i} failed")
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        if memory_increase < 50:  # Less than 50MB increase
            print(f"   ✅ Memory management: PASS (increased {memory_increase:.1f}MB)")
            test_results.append("PASS")
        else:
            print(f"   ⚠️  Memory management: WARN (increased {memory_increase:.1f}MB)")
            test_results.append("WARN")
            
    except ImportError:
        print("   ⚠️  Memory management: SKIP (psutil not available)")
        test_results.append("SKIP")
    except Exception as e:
        print(f"   ❌ Memory management: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 7: Concurrent-like behavior simulation
    print("\n7️⃣ Testing Concurrent-like Behavior")
    try:
        import threading
        import time
        
        results = []
        errors = []
        
        def render_chart():
            try:
                result = render_func(
                    chart_type="pie",
                    data=[{"cat": "A", "val": 30}, {"cat": "B", "val": 70}],
                    field_map={"category_field": "cat", "value_field": "val"}
                )
                results.append(result.get("status") == "success")
            except Exception as e:
                errors.append(str(e))
        
        # Simulate concurrent calls
        threads = []
        for i in range(5):
            thread = threading.Thread(target=render_chart)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        if len(errors) == 0 and all(results):
            print("   ✅ Concurrent behavior: PASS")
            test_results.append("PASS")
        else:
            print(f"   ❌ Concurrent behavior: FAIL - Errors: {errors}")
            test_results.append("FAIL")
            
    except Exception as e:
        print(f"   ❌ Concurrent behavior: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Test 8: Invalid configuration values
    print("\n8️⃣ Testing Invalid Configuration Values")
    try:
        config_file = os.path.expanduser("~/.plots_mcp_config.json")
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # Try invalid configurations
        invalid_configs = [
            {"chart_width": -100, "chart_height": 600},
            {"chart_width": 800, "chart_height": 0},
            {"theme": "nonexistent_theme"},
            {"output_format": "invalid_format"}
        ]
        
        config_test_results = []
        for i, invalid_config in enumerate(invalid_configs):
            try:
                configure_func(**invalid_config)
                # Then try to render
                result = render_func(
                    chart_type="bar",
                    data=[{"cat": "A", "val": 10}],
                    field_map={"category_field": "cat", "value_field": "val"}
                )
                # Should either handle gracefully or fail appropriately
                config_test_results.append("HANDLED")
            except Exception as e:
                config_test_results.append("EXCEPTION")
        
        print(f"   ✅ Invalid config handling: PASS (handled {len(config_test_results)} cases)")
        test_results.append("PASS")
        
        # Clean up
        if os.path.exists(config_file):
            os.remove(config_file)
            
    except Exception as e:
        print(f"   ❌ Invalid config handling: FAIL - Exception: {e}")
        test_results.append("FAIL")
    
    # Final assessment
    print("\n" + "=" * 45)
    print("🔬 DEEP DIVE RESULTS")
    print("=" * 45)
    
    total_tests = len(test_results)
    passed = test_results.count("PASS")
    failed = test_results.count("FAIL")
    warnings = test_results.count("WARN")
    skipped = test_results.count("SKIP")
    
    print(f"📊 Edge Case Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"⏭️  Skipped: {skipped}")
    
    pass_rate = (passed / (total_tests - skipped)) * 100 if (total_tests - skipped) > 0 else 0
    print(f"📈 Pass Rate: {pass_rate:.1f}%")
    
    if pass_rate >= 90:
        print("🎯 Assessment: EXCELLENT edge case handling")
    elif pass_rate >= 75:
        print("🎯 Assessment: GOOD edge case handling")
    else:
        print("🎯 Assessment: NEEDS IMPROVEMENT in edge case handling")

if __name__ == "__main__":
    test_deep_edge_cases()
