"""
MCP Tools - Consolidated Implementation

This module provides the MCP tools using the clean, refactored architecture.
All legacy code and feature flags have been removed for clarity and maintainability.

Architecture:
- Uses ConfigurationService for thread-safe preference management
- Uses ChartRenderingService for business logic orchestration  
- Uses ChartGeneratorFactory for extensible chart generation
- Uses custom exception hierarchy for specific error handling
"""

import logging
from typing import Dict, List, Any, Optional

from ..visualization.constants import ChartConstants
from ..domain.models import ChartRequest, UserPreferences
from ..services import get_config_service
from ..services.chart_service import ChartRenderingService

logger = logging.getLogger(__name__)

# Global service instances (initialized on first use)
_chart_service: Optional[ChartRenderingService] = None


def _get_chart_service() -> ChartRenderingService:
    """Get or create chart rendering service."""
    global _chart_service
    if _chart_service is None:
        config_service = get_config_service()
        _chart_service = ChartRenderingService(config_service)
    return _chart_service


def _get_theme_description(theme: str) -> str:
    """Get description for a theme."""
    descriptions = {
        "default": "Clean, professional blue palette perfect for business presentations",
        "dark": "Modern dark theme with bright colors, great for dashboards", 
        "seaborn": "Statistical visualization optimized with subtle colors",
        "minimal": "Understated grayscale palette for clean, simple charts"
    }
    return descriptions.get(theme, "Unknown theme")


def _get_format_description(format_type: str) -> str:
    """Get description for an output format."""
    descriptions = {
        "mermaid": "Text-based diagrams that render directly in Cursor - perfect for quick visualization",
        "mcp_image": "High-quality PNG images with full color and styling - great for reports and presentations", 
        "mcp_text": "Scalable SVG graphics with crisp text and vector precision - ideal for web and print"
    }
    return descriptions.get(format_type, "Unknown format")


def _configure_preferences_impl(
    output_format: str = None,
    theme: str = None, 
    chart_width: int = None,
    chart_height: int = None,
    reset_to_defaults: bool = False
) -> Dict[str, Any]:
    """
    Interactive configuration tool for setting user preferences.
    
    Parameters:
    - output_format: "mermaid", "mcp_image", or "mcp_text"
    - theme: "default", "dark", "seaborn", "minimal", etc.
    - chart_width: Chart width in pixels
    - chart_height: Chart height in pixels  
    - reset_to_defaults: Reset all preferences to system defaults
    
    If no parameters provided, shows current configuration with sample.
    """
    try:
        config_service = get_config_service()
        
        if reset_to_defaults:
            prefs = config_service.reset_to_defaults()
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ **Configuration Reset**\n\nAll preferences reset to defaults:\n{_format_preferences(prefs.to_dict())}"
                }]
            }
        
        # Validate inputs before updating
        updates = {}
        
        if output_format is not None:
            if ChartConstants.OutputFormats.validate(output_format):
                updates["output_format"] = output_format
            else:
                valid_formats = ", ".join(ChartConstants.OutputFormats.all())
                raise ValueError(f"Invalid output format '{output_format}'. Valid options: {valid_formats}")
        
        if theme is not None:
            if ChartConstants.Themes.validate(theme):
                updates["theme"] = theme
            else:
                valid_themes = ", ".join(ChartConstants.Themes.all())
                raise ValueError(f"Invalid theme '{theme}'. Valid options: {valid_themes}")
        
        if chart_width is not None:
            if chart_width < ChartConstants.ConfigDefaults.MIN_WIDTH or chart_width > ChartConstants.ConfigDefaults.MAX_WIDTH:
                raise ValueError(f"Chart width must be between {ChartConstants.ConfigDefaults.MIN_WIDTH} and {ChartConstants.ConfigDefaults.MAX_WIDTH}")
            updates["chart_width"] = chart_width
        
        if chart_height is not None:
            if chart_height < ChartConstants.ConfigDefaults.MIN_HEIGHT or chart_height > ChartConstants.ConfigDefaults.MAX_HEIGHT:
                raise ValueError(f"Chart height must be between {ChartConstants.ConfigDefaults.MIN_HEIGHT} and {ChartConstants.ConfigDefaults.MAX_HEIGHT}")
            updates["chart_height"] = chart_height
        
        # Show current config if no updates
        if not updates:
            current_prefs = config_service.get_user_preferences()
            return {
                "content": [{
                    "type": "text",
                    "text": f"📊 **Current Configuration**\n\n{_format_preferences(current_prefs.to_dict())}\n\n{_get_config_guide()}"
                }]
            }
        
        # Update preferences
        updated_prefs = config_service.update_preferences(**updates)
        
        return {
            "content": [{
                "type": "text",
                "text": f"✅ **Configuration Updated**\n\n{_format_preferences(updated_prefs.to_dict())}"
            }]
        }
        
    except Exception as e:
        logger.error(f"configure_preferences failed: {e}")
        return {"status": "error", "error": str(e)}


def _render_chart_impl(
    chart_type: str,
    data: List[Dict[str, Any]] = None,
    field_map: Dict[str, str] = None,
    config_overrides: Dict[str, Any] = None,
    options: Dict[str, Any] = None,
    output_format: str = None
) -> Dict[str, Any]:
    """
    Render a chart from tabular data and return MCP-compatible content.
    
    Special modes:
    - chart_type="help": Returns available chart types, themes, and field suggestions
    - chart_type="suggest": Analyzes your data and suggests field mappings (requires data)

    Parameters:
    - chart_type: chart type ("line", "bar", "pie", etc.) or "help"/"suggest"
    - data: list of objects (rows) - optional for help mode
    - field_map: keys like x_field, y_field, category_field, value_field, group_field, size_field
    - config_overrides: subset of ChartConfig as dict (width, height, title, theme, dpi, etc.)
    - options: generator-specific options (e.g., smooth, stack)
    - output_format: MCP_IMAGE (PNG), MCP_TEXT (SVG), or MERMAID
    """
    try:
        # Create chart request from parameters
        request = ChartRequest.from_tool_params(
            chart_type=chart_type,
            data=data,
            field_map=field_map,
            config_overrides=config_overrides,
            options=options,
            output_format=output_format
        )
        
        # Use chart service
        chart_service = _get_chart_service()
        response = chart_service.render_chart(request)
        
        # Convert to MCP format
        return response.to_mcp_format()
        
    except Exception as e:
        logger.error(f"render_chart failed: {e}")
        return {"status": "error", "error": str(e)}


def _format_preferences(prefs: Dict[str, Any]) -> str:
    """Format preferences for display."""
    formatted = []
    for key, value in prefs.items():
        # Add descriptions for better UX
        if key == "theme":
            desc = _get_theme_description(value)
            formatted.append(f"- **{key.replace('_', ' ').title()}**: `{value}` - {desc}")
        elif key == "output_format":
            desc = _get_format_description(value)
            formatted.append(f"- **{key.replace('_', ' ').title()}**: `{value}` - {desc}")
        else:
            formatted.append(f"- **{key.replace('_', ' ').title()}**: `{value}`")
    return "\n".join(formatted)


def _get_config_guide() -> str:
    """Get user-focused configuration guide."""
    return f"""## 🎛️ **Available Options**

### **Output Formats** (Where will you use your charts?)
- **`{ChartConstants.OutputFormats.MERMAID}`** - Shows directly in Cursor (great for quick analysis)
- **`{ChartConstants.OutputFormats.MCP_IMAGE}`** - High-quality images for presentations
- **`{ChartConstants.OutputFormats.MCP_TEXT}`** - Scalable graphics for web and documents

### **Visual Styles**
- **`{ChartConstants.Themes.DEFAULT}`** - {_get_theme_description('default')}
- **`{ChartConstants.Themes.DARK}`** - {_get_theme_description('dark')}
- **`{ChartConstants.Themes.SEABORN}`** - {_get_theme_description('seaborn')}
- **`{ChartConstants.Themes.MINIMAL}`** - {_get_theme_description('minimal')}

### **Chart Dimensions**
- **Width**: {ChartConstants.ConfigDefaults.MIN_WIDTH}-{ChartConstants.ConfigDefaults.MAX_WIDTH} pixels (typical: 800-1200)
- **Height**: {ChartConstants.ConfigDefaults.MIN_HEIGHT}-{ChartConstants.ConfigDefaults.MAX_HEIGHT} pixels (typical: 600-800)

### **Quick Setup Examples**
- **For exploring data**: Use `mermaid` format with `default` theme
- **For presentations**: Use `mcp_image` format with larger size (1200x800)
- **For modern dashboards**: Use `mcp_image` format with `dark` theme
- **To start fresh**: Reset all settings to defaults

**💡 Tip**: Mermaid format shows results instantly in Cursor - perfect for data exploration. Switch to image format when you need polished charts for presentations."""


def register_tools(mcp_server, config: Dict[str, Any] = None):
    """
    Register MCP tools with the server.
    
    This function registers the clean, service-based implementation of all tools.
    All legacy code and feature flags have been removed.
    
    Args:
        mcp_server: MCP server instance
        config: Optional configuration dictionary (not used in current implementation)
    """
    
    @mcp_server.tool()
    def configure_preferences(
        output_format: str = None,
        theme: str = None,
        chart_width: int = None,
        chart_height: int = None,
        reset_to_defaults: bool = False
    ) -> Dict[str, Any]:
        """
        Interactive configuration tool for setting user preferences.
        
        Parameters:
        - output_format: "mermaid", "mcp_image", or "mcp_text"
        - theme: "default", "dark", "seaborn", "minimal", etc.
        - chart_width: Chart width in pixels
        - chart_height: Chart height in pixels  
        - reset_to_defaults: Reset all preferences to system defaults
        
        If no parameters provided, shows current configuration with sample.
        """
        return _configure_preferences_impl(
            output_format=output_format,
            theme=theme,
            chart_width=chart_width,
            chart_height=chart_height,
            reset_to_defaults=reset_to_defaults
        )
    
    @mcp_server.tool()
    def render_chart(
        chart_type: str,
        data: List[Dict[str, Any]] = None,
        field_map: Dict[str, str] = None,
        config_overrides: Dict[str, Any] = None,
        options: Dict[str, Any] = None,
        output_format: str = None
    ) -> Dict[str, Any]:
        """
        Render a chart from tabular data and return MCP-compatible content.
        
        Special modes:
        - chart_type="help": Returns available chart types, themes, and field suggestions
        - chart_type="suggest": Analyzes your data and suggests field mappings (requires data)

        Parameters:
        - chart_type: chart type ("line", "bar", "pie", etc.) or "help"/"suggest"
        - data: list of objects (rows) - optional for help mode
        - field_map: keys like x_field, y_field, category_field, value_field, group_field, size_field
        - config_overrides: subset of ChartConfig as dict (width, height, title, theme, dpi, etc.)
        - options: generator-specific options (e.g., smooth, stack)
        - output_format: MCP_IMAGE (PNG), MCP_TEXT (SVG), or MERMAID
        """
        return _render_chart_impl(
            chart_type=chart_type,
            data=data,
            field_map=field_map,
            config_overrides=config_overrides,
            options=options,
            output_format=output_format
        )
    
    logger.info("MCP tools registered successfully with clean architecture")
