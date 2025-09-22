"""
Chart Rendering Service

Provides business logic for chart rendering with proper separation of concerns.
This service orchestrates chart generation by coordinating between configuration
management, validation, and the chart generation engine.

This service replaces the mixed responsibilities in the tools layer with
clean, testable business logic.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..domain.models import ChartRequest, ChartResponse, UserPreferences, ChartRequestMode
from ..domain.exceptions import (
    ChartGenerationError, ChartRenderingError, InvalidChartConfigurationError,
    ServiceOperationError, ErrorHandler
)
from ..visualization.constants import ChartConstants
from ..visualization.chart_config import ChartConfig, OutputFormat, Theme, ChartData
from ..visualization.generator import ChartGenerator
from .configuration_service import ConfigurationService
from .chart_generator_factory import get_chart_factory, ChartGeneratorFactory


class ChartRenderingService:
    """
    Service for rendering charts with proper separation of concerns.
    
    Handles the complete chart rendering workflow:
    1. Request validation
    2. Configuration management  
    3. Chart generation
    4. Response normalization
    """
    
    def __init__(self, config_service: ConfigurationService, chart_factory: ChartGeneratorFactory = None):
        """
        Initialize chart rendering service.
        
        Args:
            config_service: Configuration service for user preferences
            chart_factory: Chart generator factory (uses global instance if None)
        """
        self._config_service = config_service
        self._chart_factory = chart_factory or get_chart_factory()
        self._logger = logging.getLogger(__name__)
    
    def render_chart(self, request: ChartRequest) -> ChartResponse:
        """
        Render chart with full error handling and configuration management.
        
        Args:
            request: Complete chart rendering request
            
        Returns:
            ChartResponse: Standardized response with content or error
        """
        try:
            # Handle special modes
            if request.mode == ChartRequestMode.HELP:
                return self._generate_help_response()
            
            if request.mode == ChartRequestMode.SUGGEST:
                return self._generate_field_suggestions(request.data)
            
            # Validate request for regular chart rendering
            request.validate()
            
            # Get user preferences
            user_prefs = self._config_service.get_user_preferences()
            
            # Build chart configuration
            config = self._build_chart_config(request, user_prefs)
            
            # Build chart data
            chart_data = self._build_chart_data(request)
            
            # Generate chart using factory
            result = self._chart_factory.generate_chart(
                request.chart_type,
                chart_data=chart_data,
                config=config,
                **request.options
            )
            
            # Normalize response
            content = self._normalize_chart_result(result)
            
            return ChartResponse.success_response(
                content=content,
                metadata={
                    "chart_type": request.chart_type,
                    "data_points": len(request.data),
                    "output_format": config.output_format.value,
                    "generation_time": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # Use centralized error handling
            error_response = ErrorHandler.handle_chart_error(e, getattr(request, 'chart_type', None))
            
            # Log the error with appropriate level
            if isinstance(e, ChartGenerationError):
                self._logger.warning(f"Chart generation error: {e}")
            else:
                self._logger.error(f"Unexpected chart rendering error: {e}")
            
            return ChartResponse.error_response(
                error=error_response["error"],
                metadata={
                    "chart_type": getattr(request, 'chart_type', 'unknown'),
                    "error_code": error_response.get("error_code", "UNKNOWN_ERROR"),
                    "error_type": type(e).__name__
                }
            )
    
    def _build_chart_config(self, request: ChartRequest, user_prefs: UserPreferences) -> ChartConfig:
        """
        Build ChartConfig from request and user preferences.
        
        Args:
            request: Chart rendering request
            user_prefs: User preferences
            
        Returns:
            ChartConfig: Complete chart configuration
        """
        # Start with user preferences as base
        base_config = {
            "width": user_prefs.chart_width,
            "height": user_prefs.chart_height,
            "theme": Theme(user_prefs.theme),
        }
        
        # Determine output format (request overrides preferences)
        output_format = request.output_format or user_prefs.output_format
        if isinstance(output_format, str):
            base_config["output_format"] = OutputFormat(output_format.lower())
        else:
            base_config["output_format"] = output_format
        
        # Apply config overrides from request
        if request.config_overrides:
            # Filter to valid ChartConfig parameters
            valid_params = {
                "width", "height", "title", "x_title", "y_title", "theme", "colors",
                # Future: "background_color", "grid_color", "text_color" (TODO: implement)
                "output_format",
                "output_targets", "display_mode", "dpi", "show_grid", "show_legend"
            }
            
            filtered_overrides = {
                k: v for k, v in request.config_overrides.items() 
                if k in valid_params
            }
            
            # Handle theme conversion if needed
            if "theme" in filtered_overrides and isinstance(filtered_overrides["theme"], str):
                try:
                    filtered_overrides["theme"] = Theme(filtered_overrides["theme"])
                except ValueError:
                    # Invalid theme, use user preference
                    filtered_overrides["theme"] = Theme(user_prefs.theme)
            
            base_config.update(filtered_overrides)
        
        return ChartConfig(**base_config)
    
    def _build_chart_data(self, request: ChartRequest) -> ChartData:
        """
        Build ChartData from request.
        
        Args:
            request: Chart rendering request
            
        Returns:
            ChartData: Chart data with field mappings
        """
        # Create chart data with field mappings
        chart_data = ChartData(data=request.data)
        
        # Apply field mappings from request
        field_kwargs = request.get_field_kwargs()
        for field_name, field_value in field_kwargs.items():
            setattr(chart_data, field_name, field_value)
        
        return chart_data
    
    def _normalize_chart_result(self, result: Any) -> List[Dict[str, Any]]:
        """
        Normalize chart generation result to MCP content format.
        
        Args:
            result: Raw result from ChartGenerator
            
        Returns:
            List[Dict[str, Any]]: MCP-compatible content list
        """
        # Handle different result types from ChartGenerator
        if isinstance(result, dict) and "content" in result:
            return result["content"]
        
        if isinstance(result, (bytes, bytearray)):
            import base64
            b64 = base64.b64encode(result).decode("utf-8")
            return [{
                "type": "image", 
                "data": b64, 
                "mimeType": ChartConstants.MimeTypes.PNG
            }]
        
        if hasattr(result, "getvalue"):  # BytesIO
            import base64
            result.seek(0)
            b64 = base64.b64encode(result.getvalue()).decode("utf-8")
            return [{
                "type": "image", 
                "data": b64, 
                "mimeType": ChartConstants.MimeTypes.PNG
            }]
        
        if isinstance(result, str):
            # Check if it's a data URI
            if result.startswith("data:image"):
                try:
                    b64 = result.split(",", 1)[1]
                except Exception:
                    b64 = result
                return [{
                    "type": "image", 
                    "data": b64, 
                    "mimeType": ChartConstants.MimeTypes.PNG
                }]
            
            # Check if it's Mermaid syntax
            elif result.strip().startswith(("xychart-beta", "pie title", "flowchart", "gantt")):
                return [{
                    "type": "text", 
                    "text": result
                }]
            
            # Treat as SVG or other text
            else:
                return [{
                    "type": "text", 
                    "text": result
                }]
        
        # Fallback for unknown types
        return [{
            "type": "text",
            "text": str(result)
        }]
    
    def _generate_help_response(self) -> ChartResponse:
        """Generate help information response."""
        help_content = self._build_help_content()
        return ChartResponse.success_response([{
            "type": "text",
            "text": help_content
        }])
    
    def _generate_field_suggestions(self, data: List[Dict[str, Any]]) -> ChartResponse:
        """Generate field mapping suggestions based on data."""
        if not data:
            return ChartResponse.error_response("Data is required for field suggestions")
        
        suggestions = self._analyze_data_for_suggestions(data)
        return ChartResponse.success_response([{
            "type": "text", 
            "text": suggestions
        }])
    
    def _build_help_content(self) -> str:
        """Build comprehensive help content."""
        supported_types = ", ".join(self._chart_factory.get_supported_types())
        return f"""# 📊 **Chart Generation Help**

## **Available Chart Types**
{supported_types}

## **Output Formats**
- **{ChartConstants.OutputFormats.MERMAID}**: Text-based diagrams (renders in Cursor)
- **{ChartConstants.OutputFormats.MCP_IMAGE}**: PNG images (base64 encoded)  
- **{ChartConstants.OutputFormats.MCP_TEXT}**: SVG vector graphics

## **Available Themes**
{', '.join(ChartConstants.Themes.all())}

## **Common Field Mappings**
- **x_field**: X-axis values (for line, scatter charts)
- **y_field**: Y-axis values (for line, scatter charts)
- **category_field**: Categories (for bar, pie charts)
- **value_field**: Numeric values (for bar, pie, funnel charts)
- **group_field**: Series grouping (optional)

## **Example Usage**
```json
{{
  "chart_type": "bar",
  "data": [{{"category": "A", "value": 10}}],
  "field_map": {{"category_field": "category", "value_field": "value"}},
  "output_format": "{ChartConstants.OutputFormats.MERMAID}"
}}
```

Use `chart_type="suggest"` to get field mapping suggestions for your data.
"""
    
    def _analyze_data_for_suggestions(self, data: List[Dict[str, Any]]) -> str:
        """Analyze data and suggest appropriate field mappings."""
        if not data or not isinstance(data[0], dict):
            return "Unable to analyze data structure"
        
        sample = data[0]
        columns = list(sample.keys())
        
        # Analyze column types
        numeric_fields = []
        text_fields = []
        date_fields = []
        
        for col in columns:
            sample_val = sample[col]
            if isinstance(sample_val, (int, float)):
                numeric_fields.append(col)
            elif isinstance(sample_val, str):
                # Simple date detection
                if any(date_word in col.lower() for date_word in ['date', 'time', 'year', 'month']):
                    date_fields.append(col)
                else:
                    text_fields.append(col)
        
        # Generate suggestions
        suggestions = [
            f"# 🔍 **Field Analysis for {len(data)} data points**\n",
            f"**Available columns**: {', '.join(columns)}\n",
            f"**Numeric fields**: {', '.join(numeric_fields) if numeric_fields else 'None'}",
            f"**Text fields**: {', '.join(text_fields) if text_fields else 'None'}",
            f"**Date fields**: {', '.join(date_fields) if date_fields else 'None'}\n"
        ]
        
        # Recommend chart types and field mappings
        if len(numeric_fields) >= 1 and len(text_fields) >= 1:
            suggestions.append("## **Recommended: Bar Chart**")
            suggestions.append(f"```json")
            suggestions.append(f'{{"category_field": "{text_fields[0]}", "value_field": "{numeric_fields[0]}"}}')
            suggestions.append("```\n")
        
        if len(numeric_fields) >= 2:
            suggestions.append("## **Recommended: Line/Scatter Chart**")
            suggestions.append(f"```json")
            suggestions.append(f'{{"x_field": "{numeric_fields[0]}", "y_field": "{numeric_fields[1]}"}}')
            suggestions.append("```\n")
        
        return '\n'.join(suggestions)
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for debugging."""
        return {
            "service_type": "ChartRenderingService",
            "config_service": str(self._config_service),
            "chart_factory": self._chart_factory.get_factory_info(),
            "supported_formats": list(ChartConstants.OutputFormats.all()),
            "supported_themes": list(ChartConstants.Themes.all())
        }
