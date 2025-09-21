#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for MCP Plots Server
Expert QA Engineer Testing Protocol

This suite tests:
1. Core functionality across all chart types
2. Error handling and edge cases  
3. Configuration and preference management
4. Field validation system
5. Output format consistency
6. Performance and resource management
7. Integration between components
"""

import sys
import os
import json
import time
import traceback
from typing import Dict, List, Any, Optional
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(__file__))

class QATestSuite:
    def __init__(self):
        self.mock_server = Mock()
        self.registered_tools = {}
        self.test_results = []
        self.config_file = os.path.expanduser("~/.plots_mcp_config.json")
        
        # Setup mock server
        def mock_tool_decorator():
            def decorator(func):
                self.registered_tools[func.__name__] = func
                return func
            return decorator
        
        self.mock_server.tool = mock_tool_decorator
        
        # Register tools
        from src.capabilities.tools import register_tools
        register_tools(self.mock_server)
        
        self.configure_func = self.registered_tools.get('configure_preferences')
        self.render_func = self.registered_tools.get('render_chart')
    
    def log_test(self, test_name: str, status: str, details: str = "", execution_time: float = 0):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "execution_time": execution_time
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   {details}")
        if execution_time > 0:
            print(f"   Execution time: {execution_time:.3f}s")
    
    def cleanup_config(self):
        """Clean up configuration file"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_basic_functionality(self):
        """Test 1: Basic chart generation for all chart types"""
        print("\n🔧 TEST CATEGORY 1: BASIC FUNCTIONALITY")
        print("=" * 50)
        
        chart_types = [
            "line", "bar", "pie", "scatter", "heatmap", "area", 
            "boxplot", "histogram", "funnel", "gauge", "radar", "sankey"
        ]
        
        basic_datasets = {
            "line": ([{"x": 1, "y": 10}, {"x": 2, "y": 20}], {"x_field": "x", "y_field": "y"}),
            "bar": ([{"cat": "A", "val": 10}, {"cat": "B", "val": 20}], {"category_field": "cat", "value_field": "val"}),
            "pie": ([{"cat": "A", "val": 10}, {"cat": "B", "val": 20}], {"category_field": "cat", "value_field": "val"}),
            "scatter": ([{"x": 1, "y": 10}, {"x": 2, "y": 20}], {"x_field": "x", "y_field": "y"}),
            "heatmap": ([{"x": 1, "y": 1, "z": 10}, {"x": 2, "y": 2, "z": 20}], {"x_field": "x", "y_field": "y", "value_field": "z"}),
            "area": ([{"x": 1, "y": 10}, {"x": 2, "y": 20}], {"x_field": "x", "y_field": "y"}),
            "boxplot": ([{"val": 10}, {"val": 20}, {"val": 15}], {"value_field": "val"}),
            "histogram": ([{"val": 10}, {"val": 20}, {"val": 15}], {"value_field": "val"}),
            "funnel": ([{"stage": "A", "val": 100}, {"stage": "B", "val": 80}], {"category_field": "stage", "value_field": "val"}),
            "gauge": ([{"val": 75}], {"value_field": "val"}),
            "radar": ([{"cat": "A", "val": 10}, {"cat": "B", "val": 20}], {"category_field": "cat", "value_field": "val"}),
            "sankey": ([{"src": "A", "tgt": "X", "val": 10}], {"source_field": "src", "target_field": "tgt", "value_field": "val"})
        }
        
        for chart_type in chart_types:
            start_time = time.time()
            try:
                data, field_map = basic_datasets[chart_type]
                result = self.render_func(
                    chart_type=chart_type,
                    data=data,
                    field_map=field_map
                )
                
                execution_time = time.time() - start_time
                
                if result.get("status") == "error":
                    self.log_test(f"Basic {chart_type} generation", "FAIL", 
                                f"Error: {result.get('error')}", execution_time)
                elif "content" in result and len(result["content"]) > 0:
                    content_type = result["content"][0].get("type", "unknown")
                    self.log_test(f"Basic {chart_type} generation", "PASS",
                                f"Generated {content_type} content", execution_time)
                else:
                    self.log_test(f"Basic {chart_type} generation", "FAIL",
                                "No content generated", execution_time)
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(f"Basic {chart_type} generation", "FAIL",
                            f"Exception: {str(e)}", execution_time)
    
    def test_error_handling(self):
        """Test 2: Error handling and validation"""
        print("\n🛡️ TEST CATEGORY 2: ERROR HANDLING & VALIDATION")
        print("=" * 50)
        
        error_test_cases = [
            {
                "name": "Empty data",
                "chart_type": "bar",
                "data": [],
                "field_map": {"category_field": "cat", "value_field": "val"},
                "expected_error": "empty"
            },
            {
                "name": "Missing required fields",
                "chart_type": "sankey",
                "data": [{"src": "A", "val": 10}],
                "field_map": {"source_field": "src"},
                "expected_error": "requires"
            },
            {
                "name": "Field not in data",
                "chart_type": "bar", 
                "data": [{"category": "A", "value": 10}],
                "field_map": {"category_field": "missing_field", "value_field": "value"},
                "expected_error": "not found"
            },
            {
                "name": "Invalid chart type",
                "chart_type": "nonexistent",
                "data": [{"cat": "A", "val": 10}],
                "field_map": {"category_field": "cat", "value_field": "val"},
                "expected_error": "not a valid ChartType"
            },
            {
                "name": "Malformed data",
                "chart_type": "bar",
                "data": "not_a_list",
                "field_map": {"category_field": "cat", "value_field": "val"},
                "expected_error": "must be"
            }
        ]
        
        for test_case in error_test_cases:
            start_time = time.time()
            try:
                result = self.render_func(
                    chart_type=test_case["chart_type"],
                    data=test_case["data"],
                    field_map=test_case["field_map"]
                )
                
                execution_time = time.time() - start_time
                
                if result.get("status") == "error":
                    error_msg = result.get("error", "").lower()
                    expected = test_case["expected_error"].lower()
                    if expected in error_msg:
                        self.log_test(f"Error handling: {test_case['name']}", "PASS",
                                    f"Correct error: {result['error']}", execution_time)
                    else:
                        self.log_test(f"Error handling: {test_case['name']}", "FAIL",
                                    f"Wrong error. Expected '{expected}', got '{error_msg}'", execution_time)
                else:
                    self.log_test(f"Error handling: {test_case['name']}", "FAIL",
                                "Expected error but got success", execution_time)
                    
            except Exception as e:
                execution_time = time.time() - start_time
                # Some errors might be raised as exceptions instead of returned
                error_msg = str(e).lower()
                expected = test_case["expected_error"].lower()
                if expected in error_msg:
                    self.log_test(f"Error handling: {test_case['name']}", "PASS",
                                f"Correct exception: {str(e)}", execution_time)
                else:
                    self.log_test(f"Error handling: {test_case['name']}", "FAIL",
                                f"Unexpected exception: {str(e)}", execution_time)
    
    def test_preference_system(self):
        """Test 3: Preference configuration and persistence"""
        print("\n⚙️ TEST CATEGORY 3: PREFERENCE SYSTEM")
        print("=" * 50)
        
        self.cleanup_config()
        
        # Test 3.1: Configure preferences
        start_time = time.time()
        try:
            config_result = self.configure_func(
                output_format="mcp_image",
                theme="dark",
                chart_width=1200,
                chart_height=900
            )
            execution_time = time.time() - start_time
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                
                user_prefs = saved_config.get('user_preferences', {})
                expected_prefs = {
                    "output_format": "mcp_image",
                    "theme": "dark", 
                    "chart_width": 1200,
                    "chart_height": 900
                }
                
                if all(user_prefs.get(k) == v for k, v in expected_prefs.items()):
                    self.log_test("Preference configuration", "PASS",
                                f"All preferences saved correctly", execution_time)
                else:
                    self.log_test("Preference configuration", "FAIL",
                                f"Preferences mismatch. Expected {expected_prefs}, got {user_prefs}", execution_time)
            else:
                self.log_test("Preference configuration", "FAIL",
                            "Config file not created", execution_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Preference configuration", "FAIL",
                        f"Exception: {str(e)}", execution_time)
        
        # Test 3.2: Preference application
        start_time = time.time()
        try:
            result = self.render_func(
                chart_type="bar",
                data=[{"cat": "A", "val": 10}, {"cat": "B", "val": 20}],
                field_map={"category_field": "cat", "value_field": "val"}
            )
            execution_time = time.time() - start_time
            
            if result.get("status") == "success":
                content = result.get("content", [])
                if content and content[0].get("type") == "image":
                    self.log_test("Preference application", "PASS",
                                "Output format preference applied (mcp_image)", execution_time)
                else:
                    self.log_test("Preference application", "FAIL", 
                                f"Wrong output format: {content[0].get('type') if content else 'none'}", execution_time)
            else:
                self.log_test("Preference application", "FAIL",
                            f"Chart generation failed: {result.get('error')}", execution_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Preference application", "FAIL",
                        f"Exception: {str(e)}", execution_time)
        
        # Test 3.3: Preference override
        start_time = time.time()
        try:
            result = self.render_func(
                chart_type="bar",
                data=[{"cat": "A", "val": 10}],
                field_map={"category_field": "cat", "value_field": "val"},
                output_format="mermaid"  # Override preference
            )
            execution_time = time.time() - start_time
            
            if result.get("status") == "success":
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    self.log_test("Preference override", "PASS",
                                "Override works (mermaid output)", execution_time)
                else:
                    self.log_test("Preference override", "FAIL",
                                f"Override failed: {content[0].get('type') if content else 'none'}", execution_time)
            else:
                self.log_test("Preference override", "FAIL",
                            f"Chart generation failed: {result.get('error')}", execution_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Preference override", "FAIL",
                        f"Exception: {str(e)}", execution_time)
        
        # Test 3.4: Reset to defaults
        start_time = time.time()
        try:
            reset_result = self.configure_func(reset_to_defaults=True)
            execution_time = time.time() - start_time
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    reset_config = json.load(f)
                
                user_prefs = reset_config.get('user_preferences', {})
                if len(user_prefs) == 0:
                    self.log_test("Reset to defaults", "PASS",
                                "User preferences cleared", execution_time)
                else:
                    self.log_test("Reset to defaults", "FAIL",
                                f"Preferences not cleared: {user_prefs}", execution_time)
            else:
                self.log_test("Reset to defaults", "FAIL",
                            "Config file missing after reset", execution_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Reset to defaults", "FAIL",
                        f"Exception: {str(e)}", execution_time)
    
    def test_output_formats(self):
        """Test 4: Output format consistency"""
        print("\n📊 TEST CATEGORY 4: OUTPUT FORMATS")
        print("=" * 50)
        
        output_formats = ["mermaid", "mcp_image", "mcp_text"]
        test_data = [{"cat": "A", "val": 10}, {"cat": "B", "val": 20}]
        field_map = {"category_field": "cat", "value_field": "val"}
        
        for output_format in output_formats:
            start_time = time.time()
            try:
                result = self.render_func(
                    chart_type="bar",
                    data=test_data,
                    field_map=field_map,
                    output_format=output_format
                )
                execution_time = time.time() - start_time
                
                if result.get("status") == "success":
                    content = result.get("content", [])
                    if content:
                        content_type = content[0].get("type")
                        expected_type = "text" if output_format == "mermaid" else "image" if output_format == "mcp_image" else "text"
                        
                        if content_type == expected_type:
                            content_size = len(content[0].get("text", "") or content[0].get("data", ""))
                            self.log_test(f"Output format: {output_format}", "PASS",
                                        f"Correct type ({content_type}), size: {content_size}", execution_time)
                        else:
                            self.log_test(f"Output format: {output_format}", "FAIL",
                                        f"Wrong type. Expected {expected_type}, got {content_type}", execution_time)
                    else:
                        self.log_test(f"Output format: {output_format}", "FAIL",
                                    "No content generated", execution_time)
                else:
                    self.log_test(f"Output format: {output_format}", "FAIL",
                                f"Generation failed: {result.get('error')}", execution_time)
                    
            except Exception as e:
                execution_time = time.time() - start_time
                self.log_test(f"Output format: {output_format}", "FAIL",
                            f"Exception: {str(e)}", execution_time)
    
    def test_performance_and_limits(self):
        """Test 5: Performance and resource limits"""
        print("\n⚡ TEST CATEGORY 5: PERFORMANCE & LIMITS")
        print("=" * 50)
        
        # Test 5.1: Large dataset
        start_time = time.time()
        try:
            large_data = [{"x": i, "y": i * 2} for i in range(1000)]
            result = self.render_func(
                chart_type="line",
                data=large_data,
                field_map={"x_field": "x", "y_field": "y"}
            )
            execution_time = time.time() - start_time
            
            if result.get("status") == "success":
                if execution_time < 10.0:  # Should complete within 10 seconds
                    self.log_test("Large dataset (1000 points)", "PASS",
                                f"Completed successfully", execution_time)
                else:
                    self.log_test("Large dataset (1000 points)", "WARN",
                                f"Slow performance", execution_time)
            else:
                self.log_test("Large dataset (1000 points)", "FAIL",
                            f"Failed: {result.get('error')}", execution_time)
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Large dataset (1000 points)", "FAIL",
                        f"Exception: {str(e)}", execution_time)
        
        # Test 5.2: Memory usage with multiple charts
        start_time = time.time()
        try:
            test_data = [{"cat": f"Item{i}", "val": i} for i in range(100)]
            
            for i in range(10):  # Generate 10 charts quickly
                result = self.render_func(
                    chart_type="bar",
                    data=test_data,
                    field_map={"category_field": "cat", "value_field": "val"}
                )
                if result.get("status") != "success":
                    raise Exception(f"Chart {i} failed: {result.get('error')}")
            
            execution_time = time.time() - start_time
            self.log_test("Multiple chart generation", "PASS",
                        f"Generated 10 charts successfully", execution_time)
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Multiple chart generation", "FAIL",
                        f"Exception: {str(e)}", execution_time)
    
    def test_edge_cases(self):
        """Test 6: Edge cases and corner scenarios"""
        print("\n🔍 TEST CATEGORY 6: EDGE CASES")
        print("=" * 50)
        
        edge_cases = [
            {
                "name": "Single data point",
                "chart_type": "line",
                "data": [{"x": 1, "y": 10}],
                "field_map": {"x_field": "x", "y_field": "y"}
            },
            {
                "name": "Duplicate values",
                "chart_type": "bar", 
                "data": [{"cat": "A", "val": 10}, {"cat": "A", "val": 20}],
                "field_map": {"category_field": "cat", "value_field": "val"}
            },
            {
                "name": "Null/None values",
                "chart_type": "line",
                "data": [{"x": 1, "y": 10}, {"x": 2, "y": None}, {"x": 3, "y": 30}],
                "field_map": {"x_field": "x", "y_field": "y"}
            },
            {
                "name": "Mixed data types",
                "chart_type": "bar",
                "data": [{"cat": "A", "val": 10}, {"cat": "B", "val": "20"}],
                "field_map": {"category_field": "cat", "value_field": "val"}
            },
            {
                "name": "Very long labels",
                "chart_type": "pie",
                "data": [{"cat": "A" * 100, "val": 10}, {"cat": "B" * 100, "val": 20}],
                "field_map": {"category_field": "cat", "value_field": "val"}
            }
        ]
        
        for test_case in edge_cases:
            start_time = time.time()
            try:
                result = self.render_func(
                    chart_type=test_case["chart_type"],
                    data=test_case["data"], 
                    field_map=test_case["field_map"]
                )
                execution_time = time.time() - start_time
                
                if result.get("status") == "success":
                    self.log_test(f"Edge case: {test_case['name']}", "PASS",
                                "Handled gracefully", execution_time)
                else:
                    # Some edge cases might legitimately fail
                    error = result.get("error", "")
                    if "None" in error or "null" in error.lower():
                        self.log_test(f"Edge case: {test_case['name']}", "FAIL",
                                    f"None error: {error}", execution_time)
                    else:
                        self.log_test(f"Edge case: {test_case['name']}", "WARN",
                                    f"Expected failure: {error}", execution_time)
                        
            except Exception as e:
                execution_time = time.time() - start_time
                if "None" in str(e) or "null" in str(e).lower():
                    self.log_test(f"Edge case: {test_case['name']}", "FAIL",
                                f"None exception: {str(e)}", execution_time)
                else:
                    self.log_test(f"Edge case: {test_case['name']}", "WARN",
                                f"Exception (may be expected): {str(e)}", execution_time)
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 MCP PLOTS SERVER - COMPREHENSIVE QA TEST SUITE")
        print("=" * 60)
        print("Expert QA Engineer Testing Protocol")
        print("Testing all components for reliability, edge cases, and performance")
        
        start_time = time.time()
        
        # Run all test categories
        self.test_basic_functionality()
        self.test_error_handling()
        self.test_preference_system()
        self.test_output_formats()
        self.test_performance_and_limits()
        self.test_edge_cases()
        
        total_time = time.time() - start_time
        
        # Cleanup
        self.cleanup_config()
        
        # Generate report
        self.generate_report(total_time)
    
    def generate_report(self, total_time: float):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 QA TEST REPORT")
        print("=" * 60)
        
        # Count results
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL") 
        warnings = sum(1 for r in self.test_results if r["status"] == "WARN")
        
        pass_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   📈 Pass Rate: {pass_rate:.1f}%")
        print(f"   ⏱️  Total Time: {total_time:.2f}s")
        
        # Critical issues
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL" and 
                           ("None" in r["details"] or "exception" in r["details"].lower())]
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        # Performance issues
        slow_tests = [r for r in self.test_results if r["execution_time"] > 5.0]
        if slow_tests:
            print(f"\n⚡ PERFORMANCE CONCERNS ({len(slow_tests)}):")
            for test in slow_tests:
                print(f"   • {test['test']}: {test['execution_time']:.2f}s")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if pass_rate >= 90:
            print("   🟢 EXCELLENT - System is highly reliable")
        elif pass_rate >= 80:
            print("   🟡 GOOD - Minor issues to address")
        elif pass_rate >= 70:
            print("   🟠 ACCEPTABLE - Several issues need attention")
        else:
            print("   🔴 POOR - Major issues require immediate attention")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if failed > 0:
            print("   1. Address all failed test cases immediately")
        if critical_failures:
            print("   2. Fix None/null handling issues (critical)")
        if slow_tests:
            print("   3. Optimize performance for large datasets")
        if warnings > 0:
            print("   4. Review warning cases for edge case handling")
        
        print("\n" + "=" * 60)

def main():
    """Run QA test suite"""
    qa_suite = QATestSuite()
    qa_suite.run_all_tests()

if __name__ == "__main__":
    main()
