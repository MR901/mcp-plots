
import argparse
import logging
import os
import sys
from typing import Dict, Any
from dataclasses import dataclass

from src.app.server import create_server


@dataclass
class ServerConfig:
    """Configuration for the MCP server with environment variable support."""
    
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
    def from_env_and_args(cls) -> 'ServerConfig':
        """Create configuration from environment variables and command line arguments."""
        
        # Environment variable defaults
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
        parser = argparse.ArgumentParser(description="Start the Plots MCP Server")
        parser.add_argument("-t", "--transport", default=config.transport, 
                          choices=["streamable-http", "stdio"], 
                          help="Transport for MCP server (env: MCP_TRANSPORT)")
        parser.add_argument("--host", default=config.host, type=str, 
                          help="Host address for HTTP transport (env: MCP_HOST)")
        parser.add_argument("--port", default=config.port, type=int, 
                          help="Port for HTTP transport (env: MCP_PORT)")
        parser.add_argument("--log-level", default=config.log_level, type=str,
                          choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                          help="Logging level (env: LOG_LEVEL)")
        parser.add_argument("--debug", action="store_true", default=config.debug,
                          help="Enable debug mode (env: MCP_DEBUG)")
        parser.add_argument("--chart-width", default=config.default_chart_width, type=int,
                          help="Default chart width (env: CHART_DEFAULT_WIDTH)")
        parser.add_argument("--chart-height", default=config.default_chart_height, type=int,
                          help="Default chart height (env: CHART_DEFAULT_HEIGHT)")
        parser.add_argument("--chart-dpi", default=config.default_dpi, type=int,
                          help="Default chart DPI (env: CHART_DEFAULT_DPI)")
        parser.add_argument("--max-data-points", default=config.max_data_points, type=int,
                          help="Maximum data points per chart (env: CHART_MAX_DATA_POINTS)")
        
        args = parser.parse_args()
        
        # Override config with command line arguments
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
        """Convert configuration to dictionary for logging/debugging."""
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
    """Configure logging with the specified level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point for the MCP server."""
    try:
        # Load configuration from environment and command line
        config = ServerConfig.from_env_and_args()
        
        # Configure logging
        _configure_logging(config.log_level)
        logger = logging.getLogger(__name__)
        
        # Log configuration
        logger.info("Starting Plots MCP Server...")
        logger.info(f"Configuration: {config.to_dict()}")
        
        # Create and configure server
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
        
        # Setup and run server
        server.setup_mcp_server_and_capabilities()
        server.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.critical(f"Server failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
