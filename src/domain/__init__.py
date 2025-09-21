"""
Domain Models Module

Contains domain-specific data models, value objects, and business entities
for the MCP Plots Server. These models provide type safety and validation
for chart generation requests and configuration management.
"""

from .models import UserPreferences, ChartRequest, ChartResponse

__all__ = ["UserPreferences", "ChartRequest", "ChartResponse"]
