"""
Domain models for chart generation and configuration.

This module defines strongly-typed data models that replace generic
Dict[str, Any] types throughout the codebase. These models provide
validation, type safety, and clear contracts between components.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from enum import Enum

from ..visualization.constants import ChartConstants


class ChartRequestMode(Enum):
    """Special modes for chart requests"""
    RENDER = "render"
    HELP = "help"
    SUGGEST = "suggest"


@dataclass
class UserPreferences:
    """
    User configuration preferences with validation.
    
    Represents user's saved preferences for chart generation,
    including output format, styling, and dimensions.
    """
    output_format: str = ChartConstants.ConfigDefaults.OUTPUT_FORMAT
    theme: str = ChartConstants.ConfigDefaults.THEME
    chart_width: int = ChartConstants.ConfigDefaults.WIDTH
    chart_height: int = ChartConstants.ConfigDefaults.HEIGHT
    
    def __post_init__(self):
        """Validate preferences after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate all preference values"""
        if not ChartConstants.OutputFormats.validate(self.output_format):
            raise ValueError(f"Invalid output format: {self.output_format}")
        
        if not ChartConstants.Themes.validate(self.theme):
            raise ValueError(f"Invalid theme: {self.theme}")
        
        ChartConstants.validate_config_values(
            self.chart_width, 
            self.chart_height, 
            ChartConstants.ConfigDefaults.DPI
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary for serialization"""
        return {
            "output_format": self.output_format,
            "theme": self.theme,
            "chart_width": self.chart_width,
            "chart_height": self.chart_height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create preferences from dictionary with defaults"""
        return cls(
            output_format=data.get("output_format", ChartConstants.ConfigDefaults.OUTPUT_FORMAT),
            theme=data.get("theme", ChartConstants.ConfigDefaults.THEME),
            chart_width=data.get("chart_width", ChartConstants.ConfigDefaults.WIDTH),
            chart_height=data.get("chart_height", ChartConstants.ConfigDefaults.HEIGHT)
        )
    
    def merge_with_overrides(self, overrides: Dict[str, Any]) -> 'UserPreferences':
        """Create new preferences by merging with overrides"""
        merged_data = self.to_dict()
        
        # Map override keys to preference keys
        key_mapping = {
            "width": "chart_width",
            "height": "chart_height",
            "output_format": "output_format",
            "theme": "theme"
        }
        
        for override_key, value in overrides.items():
            pref_key = key_mapping.get(override_key, override_key)
            if pref_key in merged_data:
                merged_data[pref_key] = value
        
        return UserPreferences.from_dict(merged_data)


@dataclass
class FieldMapping:
    """
    Chart field mappings with validation.
    
    Maps chart concepts (x-axis, y-axis, etc.) to actual data column names.
    Provides validation that required fields are present.
    """
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    category_field: Optional[str] = None
    value_field: Optional[str] = None
    group_field: Optional[str] = None
    size_field: Optional[str] = None
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    # Future implementations:
    # name_field: Optional[str] = None      # TODO: implement entity naming
    # time_field: Optional[str] = None      # TODO: implement temporal data
    
    @classmethod
    def from_dict(cls, field_map: Dict[str, str]) -> 'FieldMapping':
        """Create field mapping from dictionary"""
        return cls(
            x_field=field_map.get(ChartConstants.FieldNames.X_FIELD),
            y_field=field_map.get(ChartConstants.FieldNames.Y_FIELD),
            category_field=field_map.get(ChartConstants.FieldNames.CATEGORY_FIELD),
            value_field=field_map.get(ChartConstants.FieldNames.VALUE_FIELD),
            group_field=field_map.get(ChartConstants.FieldNames.GROUP_FIELD),
            size_field=field_map.get(ChartConstants.FieldNames.SIZE_FIELD),
            source_field=field_map.get(ChartConstants.FieldNames.SOURCE_FIELD),
            target_field=field_map.get(ChartConstants.FieldNames.TARGET_FIELD)
            # Future: name_field, time_field will be added when implemented
        )
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary, excluding None values"""
        result = {}
        for field_name in ChartConstants.FieldNames.all():
            value = getattr(self, field_name, None)
            if value is not None:
                result[field_name] = value
        return result
    
    def get_non_none_fields(self) -> Dict[str, str]:
        """Get only fields that have values"""
        return {k: v for k, v in self.to_dict().items() if v is not None}


@dataclass
class ChartRequest:
    """
    Complete chart generation request with validation.
    
    Encapsulates all information needed to generate a chart,
    including data, configuration, and output preferences.
    """
    chart_type: str
    data: List[Dict[str, Any]]
    field_mapping: FieldMapping = field(default_factory=FieldMapping)
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    output_format: Optional[str] = None
    mode: ChartRequestMode = ChartRequestMode.RENDER
    
    def __post_init__(self):
        """Validate request after initialization"""
        # Only validate for render mode, not for help/suggest
        if self.mode == ChartRequestMode.RENDER:
            self.validate()
    
    @classmethod
    def from_tool_params(
        cls,
        chart_type: str,
        data: Optional[List[Dict[str, Any]]] = None,
        field_map: Optional[Dict[str, str]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        output_format: Optional[str] = None
    ) -> 'ChartRequest':
        """Create request from MCP tool parameters"""
        
        # Determine mode based on chart_type
        if chart_type == "help":
            mode = ChartRequestMode.HELP
        elif chart_type == "suggest":
            mode = ChartRequestMode.SUGGEST
        else:
            mode = ChartRequestMode.RENDER
        
        return cls(
            chart_type=chart_type,
            data=data or [],
            field_mapping=FieldMapping.from_dict(field_map or {}),
            config_overrides=config_overrides or {},
            options=options or {},
            output_format=output_format,
            mode=mode
        )
    
    def validate(self) -> None:
        """Validate request for chart generation"""
        if self.mode == ChartRequestMode.RENDER:
            if not self.data:
                raise ValueError(ChartConstants.ErrorMessages.EMPTY_DATA)
            
            if not isinstance(self.data, list):
                raise ValueError(ChartConstants.ErrorMessages.INVALID_DATA_TYPE)
            
            if len(self.data) > ChartConstants.ConfigDefaults.MAX_DATA_POINTS:
                raise ValueError(f"Data exceeds maximum allowed points: {ChartConstants.ConfigDefaults.MAX_DATA_POINTS}")
        
        elif self.mode == ChartRequestMode.SUGGEST:
            if not self.data:
                raise ValueError("Data is required for field suggestions")
    
    def get_field_kwargs(self) -> Dict[str, Any]:
        """Get field mappings as kwargs for ChartGenerator"""
        return self.field_mapping.get_non_none_fields()
    
    def is_special_mode(self) -> bool:
        """Check if this is a special mode request (help/suggest)"""
        return self.mode in (ChartRequestMode.HELP, ChartRequestMode.SUGGEST)


@dataclass
class ChartResponse:
    """
    Standardized chart generation response.
    
    Provides consistent response format for all chart generation
    operations, including success and error cases.
    """
    success: bool
    content: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_response(
        cls, 
        content: List[Dict[str, Any]], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ChartResponse':
        """Create successful response"""
        return cls(
            success=True,
            content=content,
            metadata=metadata or {}
        )
    
    @classmethod
    def error_response(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> 'ChartResponse':
        """Create error response"""
        return cls(
            success=False,
            error=error,
            metadata=metadata or {}
        )
    
    def to_mcp_format(self) -> Dict[str, Any]:
        """Convert to MCP tool response format"""
        if self.success:
            result = {"status": "success"}
            if self.content:
                result["content"] = self.content
            return result
        else:
            return {
                "status": "error",
                "error": self.error or "Unknown error"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class ConfigurationSnapshot:
    """
    Snapshot of current configuration state.
    
    Used for debugging and monitoring configuration changes.
    """
    user_preferences: UserPreferences
    effective_config: Dict[str, Any]
    timestamp: str
    source: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "user_preferences": self.user_preferences.to_dict(),
            "effective_config": self.effective_config,
            "timestamp": self.timestamp,
            "source": self.source
        }
