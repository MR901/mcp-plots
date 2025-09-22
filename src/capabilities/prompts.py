"""
MCP Prompts for Visualization Workflows

This module registers prompts that provide guidance and instructions for using
the chart generation capabilities. Prompts help MCP clients understand how to
effectively use the visualization tools and follow best practices.

The prompts serve as built-in documentation that can be accessed by MCP clients
to get contextual help and usage examples for chart generation workflows.
"""

from __future__ import annotations

from typing import Dict, Any, Optional


def register_prompts(mcp_server, config: Optional[Dict[str, Any]] = None):
    """
    Register visualization workflow prompts with the MCP server.
    
    Adds helpful prompts that guide users through chart generation workflows,
    including tool usage instructions, field mapping guidance, and best practices.
    
    Args:
        mcp_server: The FastMCP server instance to register prompts with
        config: Optional configuration dictionary (currently unused)
    """

    # Comprehensive workflow guide for chart generation
    GUIDE = (
        "You can render charts from tabular data using tools.\n"
        "Workflow:\n"
        "1) Call list_chart_types to see available chart types.\n"
        "2) If unsure about fields, call suggest_fields with a few sample rows.\n"
        "3) Call render_chart with: chart_type, data (list of rows), field_map (e.g., x_field,y_field or category_field,value_field),\n"
        "   and optional config_overrides (width,height,title,theme,dpi,output_format=MCP_IMAGE or MCP_TEXT).\n"
        "Notes:\n"
        "- Keep datasets small for responsiveness (you can sample ~200-500 rows).\n"
        "- Use MCP_IMAGE for PNG output (recommended for chat), or MCP_TEXT for SVG.\n"
        "- For grouped series, include group_field. For Sankey, include source_field,target_field,value_field.\n"
    )

    @mcp_server.prompt()
    def visualization_guide() -> str:
        """
        Comprehensive instructions for using visualization tools in this MCP server.
        
        Provides step-by-step workflow guidance for generating charts from data,
        including tool usage patterns, field mapping strategies, and optimization
        tips for the best user experience.
        
        Returns:
            str: Detailed workflow instructions and best practices
        """
        return GUIDE


