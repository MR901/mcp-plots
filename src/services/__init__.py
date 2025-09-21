"""
Services Module

Contains business logic services that handle core application functionality.
Services provide a clean separation between the MCP tools layer and the
underlying chart generation and configuration management.

This module uses a simple service locator pattern during the migration
to avoid breaking existing code while introducing proper dependency injection.
"""

from typing import Optional
from .configuration_service import ConfigurationService

# Global service instances (transitional pattern during refactoring)
_config_service: Optional[ConfigurationService] = None


def get_config_service() -> ConfigurationService:
    """
    Get or create configuration service singleton.
    
    This is a transitional pattern to avoid breaking existing code
    while introducing proper service architecture. In the future,
    this should be replaced with proper dependency injection.
    
    Returns:
        ConfigurationService: The global configuration service instance
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigurationService()
    return _config_service


def set_config_service(service: ConfigurationService) -> None:
    """
    Set configuration service instance.
    
    This is primarily used for testing to inject mock services.
    
    Args:
        service: The configuration service to use
    """
    global _config_service
    _config_service = service


def reset_services() -> None:
    """
    Reset all service instances.
    
    This is primarily used for testing to ensure clean state
    between test runs.
    """
    global _config_service
    _config_service = None


__all__ = [
    "ConfigurationService",
    "get_config_service", 
    "set_config_service",
    "reset_services"
]
