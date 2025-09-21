from __future__ import annotations

import logging
import json
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Global configuration storage
_user_config = {
    "defaults": {
        "output_format": "mermaid",
        "theme": "default", 
        "chart_width": 800,
        "chart_height": 600
    },
    "user_preferences": {}
}

def _get_config_file_path() -> str:
    """Get path for configuration file."""
    return os.path.expanduser("~/.plots_mcp_config.json")

def _load_user_config() -> None:
    """Load user configuration from file."""
    global _user_config
    config_path = _get_config_file_path()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                _user_config["user_preferences"] = saved_config.get("user_preferences", {})
                logger.info("User configuration loaded successfully")
        else:
            logger.info("No existing user configuration found, using defaults")
    except Exception as e:
        logger.warning(f"Failed to load user config: {e}, using defaults")

def _save_user_config() -> None:
    """Save user configuration to file."""
    config_path = _get_config_file_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(_user_config, f, indent=2)
        logger.info("User configuration saved successfully")
    except Exception as e:
        logger.error(f"Failed to save user config: {e}")

def _get_effective_config() -> Dict[str, Any]:
    """Get effective configuration (defaults + user overrides)."""
    effective = _user_config["defaults"].copy()
    effective.update(_user_config["user_preferences"])
    return effective


def _get_theme_description(theme: str) -> str:
    """Get description for a theme."""
    descriptions = {
        "default": "Clean, professional blue palette perfect for business presentations",
        "dark": "Modern dark theme with bright colors, great for dashboards",
        "seaborn": "Statistical visualization optimized with subtle colors",
        "minimal": "Understated grayscale palette for clean, simple charts"
    }
    return descriptions.get(theme, "Custom color theme")


def _get_help_info() -> Dict[str, Any]:
    """Return comprehensive help information about available options."""
    from src.visualization.chart_config import ChartType, Theme
    
    return {
        "status": "success",
        "help": {
            "chart_types": [t.value for t in ChartType],
            "themes": [t.value for t in Theme],
            "output_formats": ["MCP_IMAGE", "MCP_TEXT", "MERMAID"],
            "special_modes": {
                "help": "Get this help information",
                "suggest": "Analyze data and suggest field mappings"
            },
            "examples": {
                "basic_chart": {
                    "chart_type": "bar",
                    "data": [{"category": "A", "value": 10}],
                    "field_map": {"category_field": "category", "value_field": "value"}
                },
                "get_help": {
                    "chart_type": "help"
                },
                "suggest_fields": {
                    "chart_type": "suggest", 
                    "data": [{"month": "Jan", "sales": 100, "region": "North"}]
                }
            }
        }
    }


def _suggest_field_mappings(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze data and suggest field mappings."""
    if not data:
        return {"status": "error", "error": "Empty data provided"}
    
    # Simple heuristic: numeric -> candidates for y/value; non-numeric -> candidates for x/category
    first = data[0]
    numeric_fields: List[str] = []
    text_fields: List[str] = []
    date_fields: List[str] = []
    
    for key in first.keys():
        values = [row.get(key) for row in data[:10]]
        sample_values = [v for v in values if v is not None]
        
        if not sample_values:
            continue
            
        # Check if numeric
        if any(isinstance(v, (int, float)) for v in sample_values):
            numeric_fields.append(key)
        # Check if looks like a date
        elif any(isinstance(v, str) and _looks_like_date(v) for v in sample_values):
            date_fields.append(key)
        else:
            text_fields.append(key)
    
    suggestions = {
        "x_candidates": text_fields + date_fields,
        "y_candidates": numeric_fields,
        "category_candidates": text_fields,
        "value_candidates": numeric_fields,
        "time_candidates": date_fields,
        "recommended_charts": _recommend_chart_types(numeric_fields, text_fields, date_fields)
    }
    
    return {"status": "success", "suggestions": suggestions}


def _looks_like_date(value: str) -> bool:
    """Simple heuristic to detect date-like strings."""
    if not isinstance(value, str):
        return False
    date_indicators = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
                      '2020', '2021', '2022', '2023', '2024', '2025',
                      '-', '/', 'q1', 'q2', 'q3', 'q4']
    return any(indicator in value.lower() for indicator in date_indicators)


def _recommend_chart_types(numeric_fields: List[str], text_fields: List[str], date_fields: List[str]) -> List[str]:
    """Recommend chart types based on field types."""
    recommendations = []
    
    if date_fields and numeric_fields:
        recommendations.extend(["line", "area"])
    if text_fields and numeric_fields:
        recommendations.extend(["bar", "pie"])
    if len(numeric_fields) >= 2:
        recommendations.extend(["scatter", "heatmap"])
    if numeric_fields:
        recommendations.extend(["histogram", "boxplot"])
        
    return recommendations or ["bar"]  # Default fallback


def register_tools(mcp_server, config: Dict[str, Any] = None):
    """Register visualization tools into the MCP server."""

    # Lazy import heavy deps to avoid import-time failures
    from src.visualization.chart_config import ChartConfig, ChartType, OutputFormat, Theme
    from src.visualization.generator import ChartGenerator

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
        try:
            # Load current user configuration
            _load_user_config()
            
            # Handle reset to defaults
            if reset_to_defaults:
                _user_config["user_preferences"] = {}
                _save_user_config()
                return {
                    "content": [{
                        "type": "text",
                        "text": "✅ **Configuration Reset**\n\nAll preferences have been reset to system defaults:\n" + 
                               "\n".join([f"- **{k}**: `{v}`" for k, v in _user_config["defaults"].items()])
                    }]
                }
            
            # Update user preferences with provided values
            config_changed = False
            updates = {}
            
            if output_format is not None:
                valid_formats = ["mermaid", "mcp_image", "mcp_text"]
                format_lower = output_format.lower()
                if format_lower in valid_formats:
                    updates["output_format"] = format_lower
                    config_changed = True
                else:
                    return {"status": "error", "error": f"Invalid output_format: {output_format}. Must be mermaid, mcp_image, or mcp_text"}
            
            if theme is not None:
                valid_themes = [t.value for t in Theme]
                if theme in valid_themes:
                    updates["theme"] = theme
                    config_changed = True
                else:
                    return {"status": "error", "error": f"Invalid theme: {theme}. Must be one of: {', '.join(valid_themes)}"}
            
            for param, value in [
                ("chart_width", chart_width),
                ("chart_height", chart_height)
            ]:
                if value is not None:
                    updates[param] = value
                    config_changed = True
            
            # Save configuration if changed
            if config_changed:
                _user_config["user_preferences"].update(updates)
                _save_user_config()
            
            # Get effective configuration
            effective_config = _get_effective_config()
            
            response_content = []
            
            # Show current configuration
            config_text = "## 🎛️ **Current Configuration**\n\n"
            if config_changed:
                config_text += "✅ **Configuration Updated!**\n\n"
            
            config_text += "**Your Settings:**\n"
            for key, value in effective_config.items():
                source = "user" if key in _user_config["user_preferences"] else "default"
                config_text += f"- **{key}**: `{value}` *({source})*\n"
            
            config_text += f"\n**Config file**: `{_get_config_file_path()}`\n"
            
            response_content.append({
                "type": "text",
                "text": config_text
            })
            
            # Always show a sample with current settings
            demo_data = [
                {"category": "Sales", "value": 120},
                {"category": "Marketing", "value": 80}, 
                {"category": "Support", "value": 60}
            ]
            
            # Show current format example
            try:
                current_format = effective_config["output_format"]
                current_theme = effective_config["theme"]
                
                sample_cfg = ChartConfig(
                    width=effective_config.get("chart_width", 400),
                    height=effective_config.get("chart_height", 300),
                    title=f"Sample ({current_format.upper()})",
                    theme=Theme(current_theme),
                    output_format=OutputFormat(current_format)
                )
                
                result = ChartGenerator.run(
                    "bar",
                    data=demo_data,
                    config=sample_cfg,
                    category_field="category",
                    value_field="value"
                )
                
                if isinstance(result, dict) and "content" in result:
                    response_content.append({
                        "type": "text",
                        "text": f"\n## 📊 **Sample Chart with Your Settings**"
                    })
                    response_content.append(result["content"][0])
                    
            except Exception as e:
                logger.warning(f"Failed to generate sample: {e}")
            
            # Show simple configuration guide
            guide_text = f"""
## 🎛️ **Quick Configuration**

```javascript
// Set your preferred format and theme
configure_preferences({{
  output_format: "mcp_image",  // "mermaid", "mcp_image", "mcp_text"
  theme: "dark",               // "default", "dark", "seaborn", "minimal"
  chart_width: 1000
}})

// Reset to defaults
configure_preferences({{reset_to_defaults: true}})
```

### **💡 How It Works:**
✅ **Set once, use everywhere** - Your preferences apply to all future charts  
✅ **Persistent** - Settings saved to `{_get_config_file_path()}`  
✅ **Override when needed** - Use `config_overrides` in `render_chart()` for one-off changes  

**Try it**: Configure your preferences, then use `render_chart()` without specifying format/theme!
            """
            
            response_content.append({
                "type": "text", 
                "text": guide_text
            })
            
            return {"content": response_content}
            
        except Exception as e:
            logger.error(f"configure_preferences failed: {e}")
            return {"status": "error", "error": str(e)}

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
        try:
            # Handle special modes
            if chart_type == "help":
                return _get_help_info()
            
            if chart_type == "suggest":
                if not data or not isinstance(data, list):
                    return {"status": "error", "error": "data is required for field suggestions"}
                return _suggest_field_mappings(data)
            
            # Regular chart rendering
            if not isinstance(data, list) or not data:
                return {"status": "error", "error": "data must be a non-empty list of objects"}

            # Load user preferences
            _load_user_config()
            user_prefs = _get_effective_config()

            field_map = field_map or {}
            options = options or {}
            config_overrides = config_overrides or {}

            # Use user preference for output_format if not specified
            if output_format is None:
                output_format = user_prefs.get("output_format", "mermaid")

            # Build config with user preferences as base
            try:
                fmt = OutputFormat(output_format.lower())
            except Exception:
                fmt = OutputFormat(user_prefs.get("output_format", "mermaid"))

            # Filter config to only valid ChartConfig parameters
            valid_config_params = {
                'width', 'height', 'title', 'x_title', 'y_title', 'theme', 'colors',
                'background_color', 'grid_color', 'text_color', 'output_format',
                'output_targets', 'display_mode', 'dpi', 'show_grid', 'show_legend'
            }
            
            # Start with user preferences as base config
            base_config = {}
            for param in valid_config_params:
                if param in user_prefs:
                    # Map user preference keys to ChartConfig parameter names
                    config_key = param
                    if param == "chart_width":
                        config_key = "width"
                    elif param == "chart_height":
                        config_key = "height"
                    
                    if config_key in valid_config_params:
                        base_config[config_key] = user_prefs[param]
            
            # Apply user overrides on top of preferences
            filtered_config = {k: v for k, v in config_overrides.items() if k in valid_config_params}
            final_config = {**base_config, **filtered_config, "output_format": fmt}
            
            # Convert theme string to Theme enum if needed
            if 'theme' in final_config and isinstance(final_config['theme'], str):
                try:
                    from src.visualization.chart_config import Theme
                    final_config['theme'] = Theme(final_config['theme'])
                except ValueError:
                    # If invalid theme string, use user preference or default
                    final_config['theme'] = Theme(user_prefs.get('theme', 'default'))
            
            cfg = ChartConfig(**final_config)

            # Debug: print config attributes
            logger.info(f"ChartConfig created with attributes: {[attr for attr in dir(cfg) if not attr.startswith('_')]}")
            logger.info(f"show_grid attribute exists: {hasattr(cfg, 'show_grid')}")
            logger.info(f"show_grid value: {getattr(cfg, 'show_grid', 'NOT_FOUND')}")

            # Route to chart engine
            usable_kwargs = {}
            for key in [
                "x_field", "y_field", "category_field", "value_field",
                "group_field", "size_field", "source_field", "target_field", "name_field", "time_field"
            ]:
                if key in field_map:
                    usable_kwargs[key] = field_map[key]

            # Merge generator options
            usable_kwargs.update(options)

            result = ChartGenerator.run(
                chart_type,
                data=data,
                config=cfg,
                **usable_kwargs
            )

            # Normalize to MCP content
            if isinstance(result, dict) and "content" in result:
                return {"status": "success", **result}

            if isinstance(result, (bytes, bytearray)):
                import base64
                b64 = base64.b64encode(result).decode("utf-8")
                return {
                    "status": "success",
                    "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                }

            if hasattr(result, "getvalue"):
                import base64
                result.seek(0)
                b64 = base64.b64encode(result.getvalue()).decode("utf-8")
                return {
                    "status": "success",
                    "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                }

            if isinstance(result, str):
                # Assume data URI or raw base64 string for image
                if result.startswith("data:image"):
                    try:
                        b64 = result.split(",", 1)[1]
                    except Exception:
                        b64 = result
                    return {
                        "status": "success",
                        "content": [{"type": "image", "data": b64, "mimeType": "image/png"}],
                    }
                elif result.strip().startswith(("xychart-beta", "pie title", "flowchart", "gantt")):
                    # This looks like Mermaid syntax
                    return {
                        "status": "success",
                        "content": [{"type": "text", "text": result}],
                    }
                else:
                    # Treat as SVG or other textual output
                    return {
                        "status": "success",
                        "content": [{"type": "text", "text": result}],
                    }

            return {"status": "error", "error": "Unsupported chart result type"}

        except Exception as e:
            logger.error(f"render_chart failed: {e}")
            return {"status": "error", "error": str(e)}


