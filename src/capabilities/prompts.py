from __future__ import annotations

from typing import Dict, Any, Optional


def register_prompts(mcp_server, config: Optional[Dict[str, Any]] = None):
    """Register prompts for visualization workflows."""

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
        """Instructions for using visualization tools in this MCP server."""
        return GUIDE


