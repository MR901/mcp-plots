from __future__ import annotations

import os
import sys
import logging
from typing import Dict, Any

from tabulate import tabulate
from mcp.server.fastmcp import FastMCP


logger = logging.getLogger(__name__)


USE_COLORS = True
RESET = "\033[0m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
YELLOW = "\033[33m"
INDENT = "    "


class MCPServer:

    def __init__(
        self, transport_route="streamable-http", stateless_http=True,
        host="0.0.0.0", port=8000, log_level="INFO", debug=False,
        capabilities_config: Dict[str, Any]=None
    ):
        """

        transport_route: options: "streamable-http", "stdio"
        """
        # Create MCP server instance
        self.transport_route = transport_route
        self.host = host
        self.port = int(port)

        if self.transport_route == "stdio":
            self.server_args = {}
        else:
            self.server_args = {
                "stateless_http": stateless_http,
                "host": self.host,
                "port": self.port,
                "log_level": log_level,
                "debug": debug,
            }

        self.mcp_server = None
        self.mcp_registered_tools = []
        self.mcp_registered_static_resources = []
        self.mcp_registered_template_resources = []
        self.mcp_registered_prompts = []
        self.capabilities_config = capabilities_config

    def _log_mcp_summary(self):
        # Extract names
        tools = [e.name for e in self.mcp_registered_tools]
        static_resources = [e.name for e in self.mcp_registered_static_resources]
        template_resources = [e for e in self.mcp_registered_template_resources]
        prompts = [e.name for e in self.mcp_registered_prompts]

        # Header with counts and optional colors
        if USE_COLORS:
            tools_header = f"{CYAN}Tools ({len(tools)}){RESET}"
            static_resources_header = f"{MAGENTA}Resources [Static] ({len(static_resources)}){RESET}"
            template_resources_header = f"{MAGENTA}Resources [Template] ({len(template_resources)}){RESET}"
            prompts_header = f"{YELLOW}Prompts ({len(prompts)}){RESET}"
        else:
            tools_header = f"Tools ({len(tools)})"
            static_resources_header = f"Resources ({len(static_resources)})"
            template_resources_header = f"Resources2 ({len(template_resources)})"
            prompts_header = f"Prompts ({len(prompts)})"

        # Build pivot rows
        max_len = max(len(tools), len(static_resources), len(template_resources), len(prompts))
        rows = []
        for i in range(max_len):
            rows.append([
                tools[i] if i < len(tools) else "",
                static_resources[i] if i < len(static_resources) else "",
                template_resources[i] if i < len(template_resources) else "",
                prompts[i] if i < len(prompts) else ""
            ])

        # Create table with fancy_grid style (header separator as =)
        table_str = tabulate(
            rows,
            headers=[
                tools_header, static_resources_header,
                template_resources_header, prompts_header
            ],
            tablefmt="fancy_grid"  # Shows = separator under headers
        )

        # Add indentation to every line
        table_str = (
            "Registered capabilities in MCP server.\n" +
            "\n".join(INDENT + line for line in table_str.splitlines())
        )

        logger.info("\n" + table_str)

    def _register_capabilities(self, capabilities_config):
        """Register tools, resources, and prompts with the MCP server."""
        _error = False

        # Import and register the capabilities
        try:
            # Local tools registration
            from src.capabilities.tools import register_tools
            register_tools(self.mcp_server, config=capabilities_config)

            # Attempt to list registered tools (implementation-dependent)
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

        try:
            # Local prompts registration
            from src.capabilities.prompts import register_prompts
            register_prompts(self.mcp_server, config=capabilities_config)

            try:
                self.mcp_registered_prompts = self.mcp_server._prompt_manager.list_prompts()
            except Exception:
                self.mcp_registered_prompts = []
            logger.info("MCP prompts registration complete.")

        except Exception as e:
            _msg = f"Failed to register MCP Prompts: {e}"
            logger.error(_msg)
            _error = True

        if _error:
            raise Exception("Error/s observed during MCP capabilities registration.")

    def setup_mcp_server_and_capabilities(self):
        """Setup and start the MCP server."""
        # Initialize MCP server
        logger.info("=" * 60)
        logger.info(f"MCP FastMCP module: `{FastMCP.__module__}`")
        logger.info(f"Python version: `{sys.version}`")

        if sys.version_info < (3, 10):
            raise Exception(
                "Python versions lower than 3.10 are not supported by the MCP server. "
                f"Current python version: {sys.version}"
            )
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

        # Register tools, resources, and prompts
        try:
            self._register_capabilities(self.capabilities_config)
        except Exception as e:
            _msg = f"Error: Failed to register mcp capabilities. {e} Continuing ..."
            logger.error(_msg)
        finally:
            self._log_mcp_summary()

    def run(self):
        """Run server with either `streamable-http` or `stdio` transport."""
        logger.info(f"Starting MCP Server with `{self.transport_route}` transport ...")
        if self.transport_route == "streamable-http":
            logger.info(f"Server will be available at `{self.host}:{self.port}`")

        self.mcp_server.run(transport=self.transport_route)
        logger.info("Server stopped.")


def create_server(config: Dict[str, Any] | None = None) -> MCPServer:
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



