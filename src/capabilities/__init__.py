"""
MCP Capabilities Module

Contains all MCP tools and prompts for chart generation functionality.
Provides the interface between MCP clients and the visualization engine.

This module includes:
- Chart rendering tools with multiple output formats
- Configuration tools for user preferences
- Data analysis and field mapping suggestions
- Visualization workflow prompts and guidance

The capabilities are automatically registered with the MCP server and provide
a comprehensive set of data visualization functions accessible via natural
language prompts from MCP clients.

Main Modules:
    tools: MCP tools for chart rendering and configuration
    prompts: MCP prompts for visualization workflows and guidance

Key Features:
    - Support for 12+ chart types (bar, line, pie, scatter, etc.)
    - Multiple output formats (Mermaid, PNG, SVG)  
    - Intelligent field mapping suggestions
    - Persistent user preferences
    - Comprehensive help and documentation
"""