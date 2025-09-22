"""
Centralized constants for chart generation.

This module eliminates magic strings throughout the codebase and provides
a single source of truth for all chart-related constants. This improves
maintainability, reduces typos, and makes refactoring easier.
"""

from typing import Set, Dict, Any


class ChartConstants:
    """Centralized constants for chart generation"""
    
    class OutputFormats:
        """Valid output format constants"""
        MERMAID = "mermaid"
        MCP_IMAGE = "mcp_image"
        MCP_TEXT = "mcp_text"
        
        @classmethod
        def all(cls) -> Set[str]:
            """Get all valid output formats"""
            return {cls.MERMAID, cls.MCP_IMAGE, cls.MCP_TEXT}
        
        @classmethod
        def validate(cls, format_str: str) -> bool:
            """Check if format string is valid"""
            return format_str in cls.all()
    
    class Themes:
        """Valid theme constants"""
        DEFAULT = "default"
        DARK = "dark"
        SEABORN = "seaborn"
        MINIMAL = "minimal"
        
        @classmethod
        def all(cls) -> Set[str]:
            """Get all valid themes"""
            return {cls.DEFAULT, cls.DARK, cls.SEABORN, cls.MINIMAL}
        
        @classmethod
        def validate(cls, theme_str: str) -> bool:
            """Check if theme string is valid"""
            return theme_str in cls.all()
    
    class FieldNames:
        """Chart field mapping constants"""
        X_FIELD = "x_field"
        Y_FIELD = "y_field"
        CATEGORY_FIELD = "category_field"
        VALUE_FIELD = "value_field"
        GROUP_FIELD = "group_field"
        SIZE_FIELD = "size_field"
        SOURCE_FIELD = "source_field"
        TARGET_FIELD = "target_field"
        # Future implementations:
        # NAME_FIELD = "name_field"    # TODO: implement entity naming
        # TIME_FIELD = "time_field"    # TODO: implement temporal data
        
        @classmethod
        def all(cls) -> Set[str]:
            """Get all valid field names"""
            return {
                cls.X_FIELD, cls.Y_FIELD, cls.CATEGORY_FIELD, cls.VALUE_FIELD,
                cls.GROUP_FIELD, cls.SIZE_FIELD, cls.SOURCE_FIELD, cls.TARGET_FIELD
                # Future: cls.NAME_FIELD, cls.TIME_FIELD when implemented
            }
    
    class ConfigDefaults:
        """Default configuration values"""
        WIDTH = 800
        HEIGHT = 600
        DPI = 100
        OUTPUT_FORMAT = "mermaid"  # Will be set after OutputFormats is defined
        THEME = "default"  # Will be set after Themes is defined
        CONFIG_FILE = "~/.plots_mcp_config.json"
        
        # Chart generation limits
        MAX_DATA_POINTS = 10000
        MIN_WIDTH = 100
        MAX_WIDTH = 4000
        MIN_HEIGHT = 100
        MAX_HEIGHT = 4000
        MIN_DPI = 50
        MAX_DPI = 1200
    
    class ErrorMessages:
        """Standardized error messages"""
        EMPTY_DATA = "Data cannot be empty"
        INVALID_DATA_TYPE = "Data must be a list of objects"
        INVALID_CHART_TYPE = "Invalid chart type: {chart_type}"
        MISSING_REQUIRED_FIELD = "{chart_type} chart requires {field_names}"
        FIELD_NOT_FOUND = "Field '{field_name}' not found in data columns: {available_columns}"
        INVALID_DIMENSIONS = "Width and height must be between {min_val} and {max_val}"
        INVALID_DPI = "DPI must be between {min_dpi} and {max_dpi}"
        CONFIG_LOAD_FAILED = "Failed to load configuration: {error}"
        CONFIG_SAVE_FAILED = "Failed to save configuration: {error}"
    
    class MimeTypes:
        """MIME type constants for different output formats"""
        PNG = "image/png"
        SVG = "image/svg+xml"
        TEXT = "text/plain"
        JSON = "application/json"
    
    class ChartOptions:
        """Chart-specific option constants"""
        
        class Line:
            SMOOTH = "smooth"
            SHOW_AREA = "show_area"
            SHOW_POINTS = "show_points"
            STACK = "stack"
        
        class Bar:
            HORIZONTAL = "horizontal"
            STACK = "stack"
            GROUP = "group"
        
        class Pie:
            INNER_RADIUS = "inner_radius"
            EXPLODE_LARGEST = "explode_largest"
        
        class Scatter:
            SIZE_BY_FIELD = "size_by_field"
            ALPHA = "alpha"
        
        class Heatmap:
            COLORMAP = "colormap"
            ANNOTATE = "annotate"
        
        class Boxplot:
            SHOW_OUTLIERS = "show_outliers"
        
        class Histogram:
            BINS = "bins"
            DENSITY = "density"
        
        class Funnel:
            SORT_DESCENDING = "sort_descending"
    
    @classmethod
    def validate_config_values(cls, width: int, height: int, dpi: int) -> None:
        """Validate configuration values against limits"""
        if not (cls.ConfigDefaults.MIN_WIDTH <= width <= cls.ConfigDefaults.MAX_WIDTH):
            raise ValueError(cls.ErrorMessages.INVALID_DIMENSIONS.format(
                min_val=cls.ConfigDefaults.MIN_WIDTH,
                max_val=cls.ConfigDefaults.MAX_WIDTH
            ))
        
        if not (cls.ConfigDefaults.MIN_HEIGHT <= height <= cls.ConfigDefaults.MAX_HEIGHT):
            raise ValueError(cls.ErrorMessages.INVALID_DIMENSIONS.format(
                min_val=cls.ConfigDefaults.MIN_HEIGHT,
                max_val=cls.ConfigDefaults.MAX_HEIGHT
            ))
        
        if not (cls.ConfigDefaults.MIN_DPI <= dpi <= cls.ConfigDefaults.MAX_DPI):
            raise ValueError(cls.ErrorMessages.INVALID_DPI.format(
                min_dpi=cls.ConfigDefaults.MIN_DPI,
                max_dpi=cls.ConfigDefaults.MAX_DPI
            ))


# Convenience aliases for backward compatibility during migration
OUTPUT_FORMATS = ChartConstants.OutputFormats
THEMES = ChartConstants.Themes
FIELD_NAMES = ChartConstants.FieldNames
CONFIG_DEFAULTS = ChartConstants.ConfigDefaults
ERROR_MESSAGES = ChartConstants.ErrorMessages
