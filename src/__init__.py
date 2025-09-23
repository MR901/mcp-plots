"""
MCP Plots Server Package

A Model Context Protocol (MCP) server that provides chart generation capabilities
to MCP clients like Cursor IDE. Supports multiple chart types with Mermaid-first
output for universal compatibility.

This package contains:
- MCP server implementation with FastMCP
- Chart generation tools and prompts  
- Multiple output formats (Mermaid, PNG, SVG)
- Configurable themes and styling options

Main Components:
    app: MCP server implementation and lifecycle management
    capabilities: MCP tools and prompts for chart generation
    visualization: Chart generation engines and configuration

Usage:
    # Start the server
    python -m src
    
    # Or as installed package
    mcp-plots
"""

__version__ = "0.0.2"
__author__ = "MCP Plots Team"
__description__ = "MCP server for data visualization with Mermaid-first approach"
