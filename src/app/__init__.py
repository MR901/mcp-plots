"""
MCP Server Application Module

Contains the core MCP server implementation using FastMCP. Handles server
creation, configuration, capability registration, and lifecycle management.

This module provides:
- MCPServer class for server orchestration
- Factory function for server creation
- Capability registration and summary logging
- Transport-agnostic server startup (stdio/HTTP)

The server automatically discovers and registers chart generation tools and
prompts, providing a complete data visualization service via MCP protocol.

Main Classes:
    MCPServer: Main server class with configuration and lifecycle management

Main Functions:
    create_server: Factory function for creating configured server instances
"""

from .server import MCPServer, create_server

__all__ = ["MCPServer", "create_server"]