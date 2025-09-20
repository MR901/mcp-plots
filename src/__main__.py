
import argparse
import logging
import os

from src.app.server import create_server


def _configure_logging(level: str):
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format='[%(levelname)s] %(name)s: %(message)s')


def main():
    parser = argparse.ArgumentParser(description="Start the Plots MCP Server")
    parser.add_argument("-t", "--transport", default=os.getenv("MCP_TRANSPORT", "streamable-http"), choices=["streamable-http", "stdio"], help="Transport for MCP server")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "0.0.0.0"), type=str, help="Host address (HTTP)")
    parser.add_argument("--port", default=int(os.getenv("MCP_PORT", "8000")), type=int, help="Port (HTTP)")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), type=str, help="Logging level")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    _configure_logging(args.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting Plots MCP Server ...")

    server = create_server({
        "transport": args.transport,
        "stateless_http": True,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "debug": args.debug,
        "capabilities": None,
    })

    server.setup_mcp_server_and_capabilities()
    server.run()


if __name__ == '__main__':
    main()
