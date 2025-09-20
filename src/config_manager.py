"""
CONFIGURATION MANAGEMENT

Clean configuration management for the Syinfo MCP Server.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from syinfo import Logger

logger = Logger.getlogger()



# # ============================================================================
# # ENVIRONMENT VARIABLES (for standalone mode only)
# # ============================================================================

# ============================================================================
# DEVELOPER CONSTANTS (not exposed to FogLAMP users)
# ============================================================================
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")  # Options: "streamable-http", "stdio"
MCP_STATELESS_HTTP = True
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_DEBUG = False

# ============================================================================
# MCP SERVER CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    "mcp_transport": {
        "displayName": "MCP Transport",
        "description": "Host address for the MCP server to bind to",
        "default": MCP_HOST,
    },
    "mcp_host": {
        "displayName": "MCP Server Host",
        "description": "Host address for the MCP server to bind to",
        "default": MCP_HOST,
    },
    "mcp_port": {
        "displayName": "MCP Server Port",
        "description": "Port for the MCP server to listen on",
        "default": MCP_PORT,
    },
    "log_level": {
        "displayName": "Log Level",
        "description": "Log level for diagnostic output",
        "default": "INFO",
    }

}



@dataclass
class MCPConfig:
    """Configuration data class for MCP server settings."""

    # MCP Server settings
    mcp_transport_route: str = MCP_TRANSPORT
    mcp_stateless_http: bool = MCP_STATELESS_HTTP
    mcp_host: str = MCP_HOST
    mcp_port: int = MCP_PORT
    mcp_log_level: str = "INFO"
    mcp_debug: bool = MCP_DEBUG

    # Permission settings
    allow_read_access: bool = DEFAULT_CONFIG["allow_read_access"]["default"]
    allow_write_access: bool = DEFAULT_CONFIG["allow_write_access"]["default"]
    allow_delete_access: bool = DEFAULT_CONFIG["allow_delete_access"]["default"]
    allow_direct_db_access: bool = DEFAULT_CONFIG["allow_direct_db_access"]["default"]


class ConfigManager:
    """Simple configuration manager that provides the exact structure you want."""

    def __init__(self):
        """Initialize the configuration manager."""
        self._config = MCPConfig()

    def _parse_bool(self, value: Any) -> bool:
        """Parse boolean values from various formats."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "1", "yes", "on"]
        return bool(value)

    def parse_config(self, raw_config: Dict[str, Any] = DEFAULT_CONFIG) -> None:
        """Parse FogLAMP configuration format.

        Args:
            raw_config: Raw configuration from FogLAMP
        """
        # FogLAMP connection (from service registration)
        try:
            for key, config_item in raw_config.items():
                if isinstance(config_item, dict) and "value" in config_item:
                    value = config_item["value"]

                    if key == "mcp_host":
                        self._config.mcp_host = str(value)
                    elif key == "mcp_port":
                        try:
                            self._config.mcp_port = int(value)
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid mcp_port value: {value}, using default")
                    elif key == "log_level":
                        self._config.mcp_log_level = str(value)
                    elif key == "allow_read_access":
                        self._config.allow_read_access = self._parse_bool(value)
                    elif key == "allow_write_access":
                        self._config.allow_write_access = self._parse_bool(value)
                    elif key == "allow_delete_access":
                        self._config.allow_delete_access = self._parse_bool(value)
                    elif key == "allow_direct_db_access":
                        self._config.allow_direct_db_access = self._parse_bool(value)

            logger.info(f"Configuration parsed. Permissions: READ={self._config.allow_read_access}, WRITE={self._config.allow_write_access}, DELETE={self._config.allow_delete_access}, DB_ACCESS={self._config.allow_direct_db_access}")

        except Exception as e:
            logger.error(f"Error parsing configuration: {e}. Using defaults.")

    def set_auth_token(self, auth_token: str) -> None:
        """Set authentication token from service registration.

        Args:
            auth_token: Authentication token
        """
        self._config.auth_token = auth_token

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dict.

        Returns:
            Dict[str, Any]: Configuration summary
        """
        return {
            "mcp_server": {
                "transport_route": self._config.mcp_transport_route,
                "stateless_http": self._config.mcp_stateless_http,
                "host": self._config.mcp_host,
                "port": self._config.mcp_port,
                "log_level": self._config.mcp_log_level,
                "debug": self._config.mcp_debug
            },
            "permissions": {
                "read_access": self._config.allow_read_access,
                "write_access": self._config.allow_write_access,
                "delete_access": self._config.allow_delete_access,
                "database_access": self._config.allow_direct_db_access
            }
        }
