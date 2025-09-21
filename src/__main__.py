
"""
MCP Plots Server Entry Point

Main module for the MCP (Model Context Protocol) plots server.
Handles server configuration, argument parsing, logging setup, and server lifecycle.

This server provides chart generation capabilities to MCP clients like Cursor IDE,
supporting multiple chart types (line, bar, pie, scatter, etc.) with Mermaid-first
output for universal compatibility.

Usage:
    python -m src [options]
    mcp-plots [options]
    
Examples:
    # Start with default settings (HTTP on port 8000)
    python -m src
    
    # Start with stdio transport for MCP client integration
    python -m src --transport stdio
    
    # Start with custom chart defaults
    python -m src --chart-width 1200 --chart-height 800
"""

import argparse
import logging
import os
import sys
from typing import Dict, Any
from dataclasses import dataclass

from src.app.server import create_server


@dataclass
class ServerConfig:
    """
    Configuration for the MCP server with environment variable support.
    
    This configuration class handles all server settings including transport type,
    networking options, logging configuration, and chart generation defaults.
    Settings can be provided via environment variables or command line arguments.
    
    Attributes:
        transport: MCP transport type ("streamable-http" or "stdio")
        stateless_http: Whether to use stateless HTTP mode
        host: Host address for HTTP transport (ignored for stdio)
        port: Port number for HTTP transport (ignored for stdio)
        log_level: Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        debug: Enable debug mode with verbose logging
        default_chart_width: Default width for generated charts in pixels
        default_chart_height: Default height for generated charts in pixels
        default_dpi: Default resolution for chart images
        max_data_points: Maximum number of data points allowed per chart
    """
    
    # MCP Server settings
    transport: str = "streamable-http"
    stateless_http: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    debug: bool = False
    
    # Chart generation settings  
    default_chart_width: int = 800
    default_chart_height: int = 600
    default_dpi: int = 100
    max_data_points: int = 10000
    
    @classmethod
    def from_env_and_args(cls) -> "ServerConfig":
        """
        Create configuration from environment variables and command line arguments.
        
        Reads configuration in this priority order:
        1. Command line arguments (highest priority)
        2. Environment variables 
        3. Class defaults (lowest priority)
        
        Environment Variables:
            MCP_TRANSPORT: Transport type (streamable-http, stdio)
            MCP_HOST: Host address for HTTP mode
            MCP_PORT: Port number for HTTP mode
            LOG_LEVEL: Logging level
            MCP_DEBUG: Enable debug mode (true/1/yes/on)
            CHART_DEFAULT_WIDTH: Default chart width in pixels
            CHART_DEFAULT_HEIGHT: Default chart height in pixels
            CHART_DEFAULT_DPI: Default chart DPI
            CHART_MAX_DATA_POINTS: Maximum data points per chart
            
        Returns:
            ServerConfig: Configured instance with all settings resolved
        """
        
        # Load environment variable defaults
        config = cls(
            transport=os.getenv("MCP_TRANSPORT", "streamable-http"),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=int(os.getenv("MCP_PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug=os.getenv("MCP_DEBUG", "false").lower() in ("true", "1", "yes", "on"),
            default_chart_width=int(os.getenv("CHART_DEFAULT_WIDTH", "800")),
            default_chart_height=int(os.getenv("CHART_DEFAULT_HEIGHT", "600")),
            default_dpi=int(os.getenv("CHART_DEFAULT_DPI", "100")),
            max_data_points=int(os.getenv("CHART_MAX_DATA_POINTS", "10000"))
        )
        
        # Command line argument parsing
        # Set up argument parser with comprehensive help text
        parser = argparse.ArgumentParser(description="Start the Plots MCP Server")
        
        # Transport and networking options
        parser.add_argument("-t", "--transport", default=config.transport, 
                          choices=["streamable-http", "stdio"], 
                          help="Transport for MCP server (env: MCP_TRANSPORT)")
        parser.add_argument("--host", default=config.host, type=str, 
                          help="Host address for HTTP transport (env: MCP_HOST)")
        parser.add_argument("--port", default=config.port, type=int, 
                          help="Port for HTTP transport (env: MCP_PORT)")
        
        # Logging configuration
        parser.add_argument("--log-level", default=config.log_level, type=str,
                          choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                          help="Logging level (env: LOG_LEVEL)")
        parser.add_argument("--debug", action="store_true", default=config.debug,
                          help="Enable debug mode (env: MCP_DEBUG)")
        
        # Chart generation defaults
        parser.add_argument("--chart-width", default=config.default_chart_width, type=int,
                          help="Default chart width (env: CHART_DEFAULT_WIDTH)")
        parser.add_argument("--chart-height", default=config.default_chart_height, type=int,
                          help="Default chart height (env: CHART_DEFAULT_HEIGHT)")
        parser.add_argument("--chart-dpi", default=config.default_dpi, type=int,
                          help="Default chart DPI (env: CHART_DEFAULT_DPI)")
        parser.add_argument("--max-data-points", default=config.max_data_points, type=int,
                          help="Maximum data points per chart (env: CHART_MAX_DATA_POINTS)")
        
        args = parser.parse_args()
        
        # Override config with command line arguments (highest priority)
        # This allows CLI args to override both env vars and defaults
        config.transport = args.transport
        config.host = args.host
        config.port = args.port
        config.log_level = args.log_level
        config.debug = args.debug
        config.default_chart_width = args.chart_width
        config.default_chart_height = args.chart_height
        config.default_dpi = args.chart_dpi
        config.max_data_points = args.max_data_points
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for logging and debugging.
        
        Returns:
            Dict[str, Any]: Nested dictionary with server and chart settings
                organized for easy reading in logs and debug output
        """
        return {
            "server": {
                "transport": self.transport,
                "host": self.host,
                "port": self.port,
                "log_level": self.log_level,
                "debug": self.debug
            },
            "charts": {
                "default_width": self.default_chart_width,
                "default_height": self.default_chart_height,
                "default_dpi": self.default_dpi,
                "max_data_points": self.max_data_points
            }
        }


def _configure_logging(level: str):
    """
    Configure Python logging with the specified level.
    
    Sets up a standardized logging format with timestamps, logger names,
    and message levels. Falls back to INFO level if an invalid level is provided.
    
    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level, 
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def main():
    """
    Main entry point for the MCP server.
    
    Orchestrates the complete server lifecycle:
    1. Load configuration from environment variables and CLI arguments
    2. Set up logging based on configuration
    3. Create and configure the MCP server instance
    4. Register chart generation capabilities
    5. Start the server with the specified transport
    6. Handle graceful shutdown on interruption
    
    Raises:
        SystemExit: On critical errors that prevent server startup
    """
    try:
        # Load configuration from environment and command line
        config = ServerConfig.from_env_and_args()
        
        # Configure logging based on user preferences
        _configure_logging(config.log_level)
        logger = logging.getLogger(__name__)
        
        # Log startup information for debugging
        logger.info("Starting Plots MCP Server...")
        logger.info(f"Configuration: {config.to_dict()}")
        
        # Create and configure server with resolved settings
        server = create_server({
            "transport": config.transport,
            "stateless_http": config.stateless_http,
            "host": config.host,
            "port": config.port,
            "log_level": config.log_level,
            "debug": config.debug,
            "capabilities": {
                "chart_defaults": {
                    "width": config.default_chart_width,
                    "height": config.default_chart_height,
                    "dpi": config.default_dpi,
                    "max_data_points": config.max_data_points
                }
            }
        })
        
        # Initialize MCP capabilities (tools, prompts, resources)
        server.setup_mcp_server_and_capabilities()
        
        # Start the server - this blocks until interrupted
        server.run()
        
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        logger.info("Server stopped by user.")
    except Exception as e:
        # Log critical errors and exit with error code
        logger.critical(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
