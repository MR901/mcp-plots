"""
MCP Server Implementation

This module provides the core MCP (Model Context Protocol) server implementation
using FastMCP. Handles server creation, capability registration, and lifecycle
management for the plots MCP server.

The server supports both stdio and HTTP transports, with automatic capability
discovery and registration. It provides a tabular summary of registered tools
and prompts for easier debugging.
"""

from __future__ import annotations

import os
import sys
import logging
from typing import Dict, Any

from tabulate import tabulate
from mcp.server.fastmcp import FastMCP


logger = logging.getLogger(__name__)


# Terminal color constants for enhanced logging output
USE_COLORS = True
RESET = "\033[0m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"
INDENT = "    "


class MCPServer:
    """
    MCP (Model Context Protocol) server wrapper for chart generation capabilities.
    
    This class wraps FastMCP to provide chart generation tools and prompts via
    the MCP protocol. It supports both stdio and HTTP transports, making it
    suitable for integration with various MCP clients.
    
    The server automatically discovers and registers chart generation capabilities,
    provides detailed logging, and handles graceful startup/shutdown.
    
    Attributes:
        transport_route: Transport type ("streamable-http" or "stdio")
        host: Host address for HTTP transport
        port: Port number for HTTP transport  
        mcp_server: The underlying FastMCP server instance
        mcp_registered_tools: List of registered MCP tools
        mcp_registered_prompts: List of registered MCP prompts
        capabilities_config: Configuration for chart generation capabilities
    """

    def __init__(
        self, transport_route="streamable-http", stateless_http=True,
        host="0.0.0.0", port=8000, log_level="INFO", debug=False,
        capabilities_config: Dict[str, Any]=None
    ):
        """
        Initialize the MCP server with the specified configuration.
        
        Args:
            transport_route: MCP transport type ("streamable-http" or "stdio")
            stateless_http: Whether to use stateless HTTP (ignored for stdio)
            host: Host address for HTTP transport (default: "0.0.0.0")
            port: Port number for HTTP transport (default: 8000)
            log_level: Logging level for the server (default: "INFO")
            debug: Enable debug mode with verbose logging (default: False)
            capabilities_config: Configuration dict for chart generation capabilities
        """
        # Store transport configuration
        self.transport_route = transport_route
        self.host = host
        self.port = int(port)

        # Configure server arguments based on transport type
        if self.transport_route == "stdio":
            # For stdio transport, no additional args needed
            self.server_args = {}
        else:
            # For HTTP transport, configure network settings
            self.server_args = {
                "stateless_http": stateless_http,
                "host": self.host,
                "port": self.port,
                "log_level": log_level,
                "debug": debug,
            }

        # Initialize server state
        self.mcp_server = None
        self.mcp_registered_tools = []
        self.mcp_registered_prompts = []
        self.capabilities_config = capabilities_config

    def _log_mcp_summary(self):
        """
        Log a formatted summary table of registered MCP capabilities.
        
        Creates an attractive tabular display showing all registered tools and
        prompts side-by-side. Uses terminal colors when available and provides
        counts for easy verification of capability registration.
        """
        # Extract capability names from registered objects
        tools = [e.name for e in self.mcp_registered_tools]
        prompts = [e.name for e in self.mcp_registered_prompts]

        # Create colored headers with capability counts
        if USE_COLORS:
            tools_header = f"{CYAN}Tools ({len(tools)}){RESET}"
            prompts_header = f"{YELLOW}Prompts ({len(prompts)}){RESET}"
        else:
            tools_header = f"Tools ({len(tools)})"
            prompts_header = f"Prompts ({len(prompts)})"

        # Build table rows with proper alignment
        # Each row shows one tool and one prompt side-by-side
        max_len = max(len(tools), len(prompts))
        rows = []
        for i in range(max_len):
            rows.append([
                tools[i] if i < len(tools) else "",
                prompts[i] if i < len(prompts) else ""
            ])

        # Generate table with professional formatting
        table_str = tabulate(
            rows,
            headers=[tools_header, prompts_header],
            tablefmt="fancy_grid"  # Shows = separator under headers
        )

        # Add consistent indentation and descriptive header
        table_str = (
            "Registered capabilities in MCP server.\n" +
            "\n".join(INDENT + line for line in table_str.splitlines())
        )

        logger.info("\n" + table_str)

    def _register_capabilities(self, capabilities_config):
        """
        Register chart generation tools and prompts with the MCP server.
        
        Dynamically imports and registers all available capabilities from the
        capabilities modules. Handles registration errors gracefully and maintains
        lists of successfully registered capabilities for debugging.
        
        Args:
            capabilities_config: Configuration dict passed to capability modules
            
        Raises:
            Exception: If any capability registration fails
        """
        _error = False

        # Register chart generation tools
        try:
            # Import and register visualization tools
            from src.capabilities.tools import register_tools
            register_tools(self.mcp_server, config=capabilities_config)

            # Extract registered tool list for summary display
            # Note: Uses internal API that may change in future FastMCP versions
            try:
                self.mcp_registered_tools = self.mcp_server._tool_manager.list_tools()
            except Exception:
                # Best-effort: fall back to empty list if internal API differs
                self.mcp_registered_tools = []
            logger.info("MCP tools registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Tools: {e}"
            logger.error(_msg)
            _error = True

        # Register chart generation prompts
        try:
            # Import and register visualization prompts  
            from src.capabilities.prompts import register_prompts
            register_prompts(self.mcp_server, config=capabilities_config)

            # Extract registered prompt list for summary display
            try:
                self.mcp_registered_prompts = self.mcp_server._prompt_manager.list_prompts()
            except Exception:
                # Best-effort: fall back to empty list if internal API differs
                self.mcp_registered_prompts = []
            logger.info("MCP prompts registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Prompts: {e}"
            logger.error(_msg)
            _error = True

        # Fail fast if any registration errors occurred
        if _error:
            raise Exception("Error/s observed during MCP capabilities registration.")

    def setup_mcp_server_and_capabilities(self):
        """
        Initialize the FastMCP server and register all chart generation capabilities.
        
        Performs environment validation, creates the FastMCP server instance with
        appropriate instructions, and registers all available tools and prompts.
        Logs detailed startup information for debugging.
        
        Raises:
            Exception: If Python version requirements are not met or server setup fails
        """
        # Log startup information and environment details
        logger.info("=" * 60)
        logger.info(f"MCP FastMCP module: `{FastMCP.__module__}`")
        logger.info(f"Python version: `{sys.version}`")

        # Validate Python version requirements
        if sys.version_info < (3, 10):
            raise Exception(
                "Python versions lower than 3.10 are not supported by the MCP server. "
                f"Current python version: {sys.version}"
            )
            
        # Create FastMCP server instance with chart-specific instructions
        try:
            self.mcp_server = FastMCP(
                "Plots MCP Server",
                instructions=(
                    "This server renders charts from tabular data. Use tools to generate "
                    "visualizations (line, bar, pie, scatter, heatmap, etc.) and receive results "
                    "as MCP-compatible image or text content."
                ),
                **self.server_args
            )
        except Exception as e:
            _msg = f"Failed to setup MCP server: {e}"
            logger.error(_msg)
            raise Exception(_msg)

        # Register chart generation capabilities
        try:
            self._register_capabilities(self.capabilities_config)
        except Exception as e:
            # Log error but continue - server may still be partially functional
            _msg = f"Error: Failed to register mcp capabilities. {e} Continuing ..."
            logger.error(_msg)
        finally:
            # Always show capability summary, even if some registrations failed
            self._log_mcp_summary()

    def run(self):
        """
        Start the MCP server with the configured transport.
        
        Runs the FastMCP server using either stdio or HTTP transport.
        This method blocks until the server is interrupted or stopped.
        Logs connection information for HTTP transport.
        """
        logger.info(f"Starting MCP Server with `{self.transport_route}` transport ...")
        if self.transport_route == "streamable-http":
            logger.info(f"Server will be available at `{self.host}:{self.port}`")

        # Start the server - this blocks until interrupted
        self.mcp_server.run(transport=self.transport_route)
        logger.info("Server stopped.")


def create_server(config: Dict[str, Any] | None = None) -> MCPServer:
    """
    Factory function to create a configured MCPServer instance.
    
    Provides a convenient way to create an MCP server with sensible defaults
    while allowing full configuration override via the config dictionary.
    
    Args:
        config: Configuration dictionary with server settings. Supported keys:
            - transport: Transport type ("streamable-http" or "stdio")
            - stateless_http: Use stateless HTTP mode (bool)
            - host: Host address for HTTP transport (str)
            - port: Port number for HTTP transport (int)
            - log_level: Logging level (str)
            - debug: Enable debug mode (bool)
            - capabilities: Configuration for chart generation capabilities (dict)
            
    Returns:
        MCPServer: Configured server instance ready for setup and launch
    """
    cfg = config or {}
    return MCPServer(
        transport_route=cfg.get("transport", "streamable-http"),
        stateless_http=cfg.get("stateless_http", True),
        host=cfg.get("host", "0.0.0.0"),
        port=cfg.get("port", 8000),
        log_level=cfg.get("log_level", "INFO"),
        debug=cfg.get("debug", False),
        capabilities_config=cfg.get("capabilities")
    )



