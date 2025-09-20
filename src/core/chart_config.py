
import uuid
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime
from enum import Enum
from pathlib import Path

# Graceful imports with fallbacks
try:
    import pandas as pd
except ImportError:
    pd = None
    
try:
    from matplotlib.figure import Figure
except ImportError:
    Figure = Any

# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class ChartData:
    """Enhanced data structure for chart generation with validation"""
    data: Union[List[Dict[str, Any]], 'pd.DataFrame']
    
    # Field mappings for different chart types
    x_field: Optional[str] = None
    y_field: Optional[str] = None
    category_field: Optional[str] = None
    value_field: Optional[str] = None
    group_field: Optional[str] = None
    size_field: Optional[str] = None
    
    # Specialized fields for complex charts
    source_field: Optional[str] = None  # For Sankey charts
    target_field: Optional[str] = None  # For Sankey charts
    name_field: Optional[str] = None    # For Gauge charts
    time_field: Optional[str] = None    # For time series
    
    # Metadata
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate data structure and field mappings"""
        self._validate_data()
        self._validate_field_mappings()
    
    def _validate_data(self):
        """Validate that data is in correct format"""
        if pd and isinstance(self.data, pd.DataFrame):
            if self.data.empty:
                raise ValueError("DataFrame is empty")
        elif isinstance(self.data, list):
            if not self.data:
                raise ValueError("Data list is empty")
            if not isinstance(self.data[0], dict):
                raise ValueError("Data list must contain dictionaries")
        else:
            raise TypeError("Data must be a pandas DataFrame or list of dictionaries")
    
    def _validate_field_mappings(self):
        """Validate that specified fields exist in data"""
        available_fields = self._get_available_fields()
        
        for field_name in ['x_field', 'y_field', 'category_field', 'value_field', 
                          'group_field', 'size_field', 'source_field', 'target_field', 
                          'name_field', 'time_field']:
            field_value = getattr(self, field_name)
            if field_value and field_value not in available_fields:
                raise ValueError(f"Field '{field_value}' not found in data. Available fields: {available_fields}")
    
    def _get_available_fields(self) -> List[str]:
        """Get list of available field names in the data"""
        if pd and isinstance(self.data, pd.DataFrame):
            return list(self.data.columns)
        elif isinstance(self.data, list) and self.data:
            return list(self.data[0].keys())
        return []
    
    def get_numeric_fields(self) -> List[str]:
        """Get list of numeric fields in the data"""
        if pd and isinstance(self.data, pd.DataFrame):
            return list(self.data.select_dtypes(include=['number']).columns)
        # For list of dicts, we'd need to inspect the data types
        return self._get_available_fields()  # Simplified for now
    
    def get_categorical_fields(self) -> List[str]:
        """Get list of categorical/text fields in the data"""
        if pd and isinstance(self.data, pd.DataFrame):
            return list(self.data.select_dtypes(include=['object', 'category']).columns)
        return self._get_available_fields()  # Simplified for now


# ============================================================================
# ENUMS AND CONFIGURATIONS
# ============================================================================

class ChartType(Enum):
    """Supported chart types with metadata"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    AREA = "area"
    BOXPLOT = "boxplot"
    HISTOGRAM = "histogram"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    RADAR = "radar"
    SANKEY = "sankey"
    DASHBOARD = "dashboard"  # Multi-plot dashboard
    
    @property
    def required_fields(self) -> Set[str]:
        """Get required fields for this chart type"""
        requirements = {
            self.LINE: {'x_field', 'y_field'},
            self.BAR: {'category_field', 'value_field'},
            self.PIE: {'category_field', 'value_field'},
            self.SCATTER: {'x_field', 'y_field'},
            self.HEATMAP: {'x_field', 'y_field', 'value_field'},
            self.AREA: {'x_field', 'y_field'},
            self.BOXPLOT: {'value_field'},
            self.HISTOGRAM: {'value_field'},
            self.FUNNEL: {'category_field', 'value_field'},
            self.GAUGE: {'value_field'},
            self.RADAR: {'category_field', 'value_field'},
            self.SANKEY: {'source_field', 'target_field', 'value_field'},
            self.DASHBOARD: set()  # Flexible requirements
        }
        return requirements.get(self, set())


class Theme(Enum):
    """Enhanced theme system with customization support"""
    DEFAULT = "default"
    DARK = "dark"
    SEABORN = "seaborn"
    MINIMAL = "minimal"
    CORPORATE = "corporate"
    SCIENTIFIC = "scientific"
    
    @property
    def color_palette(self) -> List[str]:
        """Get default color palette for theme"""
        palettes = {
            self.DEFAULT: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'],
            self.DARK: ['#4992ff', '#7cffb2', '#fddd60', '#ff6e76', '#58d9f9', '#05c091', '#ff8a45', '#8d48e3', '#dd79ff'],
            self.SEABORN: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22'],
            self.MINIMAL: ['#333333', '#666666', '#999999', '#cccccc', '#e6e6e6'],
            self.CORPORATE: ['#003f7f', '#0066cc', '#3399ff', '#66b3ff', '#99ccff'],
            self.SCIENTIFIC: ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd', '#5e4fa2']
        }
        return palettes.get(self, palettes[self.DEFAULT])


class OutputFormat(Enum):
    """Enhanced output formats with metadata"""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    BASE64 = "base64"
    BUFFER = "buffer"
    MCP_IMAGE = "mcp_image"
    MCP_TEXT = "mcp_text"
    HTML = "html"
    JSON = "json"
    
    @property
    def is_binary(self) -> bool:
        """Check if format produces binary output"""
        return self in [self.PNG, self.PDF, self.BUFFER]
    
    @property
    def supports_interactivity(self) -> bool:
        """Check if format supports interactive features"""
        return self in [self.HTML, self.JSON]


class DisplayMode(Enum):
    """How charts should be displayed"""
    STATIC = "static"           # Generate only, no display
    INTERACTIVE = "interactive"  # Show in popup window
    CHAT = "chat"               # Format for chat display
    HYBRID = "hybrid"           # Both interactive + chat ready
    API = "api"                 # API response format
    EMBEDDED = "embedded"       # For embedding in other applications
    

class OutputTarget(Enum):
    """Where chart output should be sent"""
    MEMORY = "memory"           # Keep in memory only
    FILE = "file"               # Save to file
    CHAT_INLINE = "chat_inline" # Inline chat display
    API_RESPONSE = "api_response" # API response
    POPUP_WINDOW = "popup_window" # Interactive popup
    CLIPBOARD = "clipboard"     # Copy to clipboard
    EMAIL = "email"             # Email attachment
    

class EnvironmentType(Enum):
    """Detected environment types"""
    JUPYTER = "jupyter"
    DESKTOP = "desktop"
    SERVER = "server"
    CONTAINER = "container"
    CLI = "cli"
    WEB = "web"
    UNKNOWN = "unknown"


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

@dataclass
class InteractiveSettings:
    """Settings for interactive display mode"""
    non_blocking: bool = True
    window_title: Optional[str] = None
    window_size: Tuple[int, int] = (800, 600)
    always_on_top: bool = False
    resizable: bool = True
    show_toolbar: bool = True
    auto_refresh: bool = False
    refresh_interval: int = 5  # seconds
    max_windows: int = 10  # Limit number of open windows


@dataclass
class ChatSettings:
    """Settings for chat display formatting"""
    max_size_kb: int = 500
    include_metadata: bool = True
    include_thumbnail: bool = True
    thumbnail_size: Tuple[int, int] = (200, 150)
    auto_compress: bool = True
    markdown_format: bool = True
    show_data_summary: bool = True
    include_download_link: bool = False


@dataclass
class FileSettings:
    """Settings for file output"""
    directory: Optional[Path] = None
    filename_template: str = "chart_{timestamp}_{id}"
    auto_increment: bool = True
    overwrite_existing: bool = False
    create_directories: bool = True
    include_timestamp: bool = True
    backup_existing: bool = False


@dataclass
class PerformanceSettings:
    """Settings for performance optimization"""
    enable_caching: bool = True
    cache_size_mb: int = 100
    parallel_processing: bool = False
    max_workers: int = 4
    memory_limit_mb: int = 500
    cleanup_threshold: int = 50  # Number of charts before cleanup
    dpi_auto_adjust: bool = True
    

@dataclass 
class ValidationSettings:
    """Settings for data validation"""
    strict_mode: bool = True
    allow_empty_data: bool = False
    auto_fix_fields: bool = True
    warn_on_missing_fields: bool = True
    validate_data_types: bool = True
    max_data_points: int = 100000
    min_data_points: int = 1


@dataclass
class ChartConfig:
    """Enhanced unified configuration for chart generation and display"""
    
    # Basic chart properties
    width: int = 800
    height: int = 600
    title: Optional[str] = None
    x_title: Optional[str] = None
    y_title: Optional[str] = None
    
    # Styling
    theme: Theme = Theme.DEFAULT
    colors: Optional[List[str]] = None
    background_color: Optional[str] = None
    grid_color: Optional[str] = None
    text_color: Optional[str] = None
    
    # Output configuration
    output_format: OutputFormat = OutputFormat.PNG
    output_targets: List[OutputTarget] = field(default_factory=lambda: [OutputTarget.MEMORY])
    dpi: int = 100
    quality: int = 95  # For lossy formats
    
    # Display configuration
    display_mode: DisplayMode = DisplayMode.STATIC
    show_legend: bool = True
    show_grid: bool = True
    legend_position: str = "best"
    grid_alpha: float = 0.3
    
    # Specialized settings
    interactive_settings: InteractiveSettings = field(default_factory=InteractiveSettings)
    chat_settings: ChatSettings = field(default_factory=ChatSettings)
    file_settings: FileSettings = field(default_factory=FileSettings)
    performance_settings: PerformanceSettings = field(default_factory=PerformanceSettings)
    validation_settings: ValidationSettings = field(default_factory=ValidationSettings)
    
    # Metadata
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration and apply smart defaults"""
        self._apply_smart_defaults()
        self._validate_configuration()
    
    def _apply_smart_defaults(self):
        """Apply intelligent defaults based on environment and usage patterns"""
        
        # Auto-detect environment
        env_type = self._detect_environment()
        
        # Adjust defaults based on environment
        if env_type == EnvironmentType.JUPYTER:
            self.display_mode = DisplayMode.STATIC  # Jupyter handles display
            self.output_format = OutputFormat.PNG
        elif env_type == EnvironmentType.SERVER:
            self.display_mode = DisplayMode.STATIC
            self.interactive_settings.non_blocking = False
        elif env_type == EnvironmentType.DESKTOP:
            if DisplayMode.STATIC == self.display_mode:  # Only change if still default
                self.display_mode = DisplayMode.INTERACTIVE
        
        # Auto-adjust DPI based on output targets
        if OutputTarget.CHAT_INLINE in self.output_targets:
            if self.dpi > 150:  # Limit DPI for chat to reduce file size
                self.dpi = 150
        
        # Apply theme-specific defaults
        if not self.colors:
            self.colors = self.theme.color_palette
    
    def _detect_environment(self) -> EnvironmentType:
        """Detect the current environment"""
        try:
            # Check for Jupyter
            if 'ipykernel' in sys.modules:
                return EnvironmentType.JUPYTER
            
            # Check for container
            if os.path.exists('/.dockerenv'):
                return EnvironmentType.CONTAINER
            
            # Check for GUI availability
            if 'DISPLAY' not in os.environ and sys.platform.startswith('linux'):
                return EnvironmentType.SERVER
            
            # Check for CLI
            if not sys.stdin.isatty():
                return EnvironmentType.CLI
                
            return EnvironmentType.DESKTOP
            
        except Exception:
            return EnvironmentType.UNKNOWN
    
    def _validate_configuration(self):
        """Validate configuration consistency"""
        
        # Validate dimensions
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Width and height must be positive")
        
        if self.width > 10000 or self.height > 10000:
            raise ValueError("Width and height must be reasonable (<=10000)")
        
        # Validate DPI
        if self.dpi <= 0 or self.dpi > 1200:
            raise ValueError("DPI must be between 1 and 1200")
        
        # Validate output targets compatibility
        if OutputTarget.POPUP_WINDOW in self.output_targets:
            if self.display_mode == DisplayMode.STATIC:
                raise ValueError("Cannot use POPUP_WINDOW target with STATIC display mode")
        
        # Validate chat settings
        if OutputTarget.CHAT_INLINE in self.output_targets:
            if self.chat_settings.max_size_kb <= 0:
                raise ValueError("Chat max_size_kb must be positive")
    
    def get_effective_colors(self) -> List[str]:
        """Get the effective color palette (custom or theme default)"""
        return self.colors if self.colors else self.theme.color_palette
    
    def supports_interactivity(self) -> bool:
        """Check if current configuration supports interactive features"""
        return (
            self.display_mode in [DisplayMode.INTERACTIVE, DisplayMode.HYBRID] or
            OutputTarget.POPUP_WINDOW in self.output_targets or
            self.output_format.supports_interactivity
        )
    
    def requires_gui(self) -> bool:
        """Check if configuration requires GUI environment"""
        return (
            OutputTarget.POPUP_WINDOW in self.output_targets or
            self.display_mode == DisplayMode.INTERACTIVE
        )
    
    def clone(self, **overrides) -> 'ChartConfig':
        """Create a copy of this configuration with optional overrides"""
        # Create a new config with current values
        config_dict = {
            'width': self.width,
            'height': self.height,
            'title': self.title,
            'x_title': self.x_title,
            'y_title': self.y_title,
            'theme': self.theme,
            'colors': self.colors.copy() if self.colors else None,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'text_color': self.text_color,
            'output_format': self.output_format,
            'output_targets': self.output_targets.copy(),
            'dpi': self.dpi,
            'quality': self.quality,
            'display_mode': self.display_mode,
            'show_legend': self.show_legend,
            'show_grid': self.show_grid,
            'legend_position': self.legend_position,
            'grid_alpha': self.grid_alpha,
            # Note: We create new instances of settings to avoid shared references
            'interactive_settings': InteractiveSettings(**self.interactive_settings.__dict__),
            'chat_settings': ChatSettings(**self.chat_settings.__dict__),
            'file_settings': FileSettings(**self.file_settings.__dict__),
            'performance_settings': PerformanceSettings(**self.performance_settings.__dict__),
            'validation_settings': ValidationSettings(**self.validation_settings.__dict__),
            'created_by': self.created_by,
            'description': self.description,
            'tags': self.tags.copy()
        }
        
        # Apply overrides
        config_dict.update(overrides)
        
        return ChartConfig(**config_dict)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_config_for_environment(env_type: EnvironmentType = None, **kwargs) -> ChartConfig:
    """Create optimized configuration for specific environment"""
    
    if env_type is None:
        config = ChartConfig(**kwargs)
        return config  # Auto-detection will happen in __post_init__
    
    # Environment-specific defaults
    env_defaults = {
        EnvironmentType.JUPYTER: {
            'display_mode': DisplayMode.STATIC,
            'output_format': OutputFormat.PNG,
            'interactive_settings': InteractiveSettings(non_blocking=False)
        },
        EnvironmentType.SERVER: {
            'display_mode': DisplayMode.STATIC,
            'output_targets': [OutputTarget.MEMORY],
            'interactive_settings': InteractiveSettings(non_blocking=False)
        },
        EnvironmentType.DESKTOP: {
            'display_mode': DisplayMode.INTERACTIVE,
            'output_targets': [OutputTarget.POPUP_WINDOW],
        },
        EnvironmentType.CONTAINER: {
            'display_mode': DisplayMode.STATIC,
            'output_format': OutputFormat.BASE64,
            'performance_settings': PerformanceSettings(memory_limit_mb=200)
        }
    }
    
    defaults = env_defaults.get(env_type, {})
    defaults.update(kwargs)
    
    return ChartConfig(**defaults)


def create_chat_optimized_config(**kwargs) -> ChartConfig:
    """Create configuration optimized for chat display"""
    # Handle chat_settings parameter correctly
    chat_settings_kwargs = kwargs.pop('chat_settings', {})
    if isinstance(chat_settings_kwargs, dict):
        chat_settings = ChatSettings(
            max_size_kb=chat_settings_kwargs.get('max_size_kb', 400),
            auto_compress=chat_settings_kwargs.get('auto_compress', True),
            include_thumbnail=chat_settings_kwargs.get('include_thumbnail', True),
            include_metadata=chat_settings_kwargs.get('include_metadata', True)
        )
    else:
        chat_settings = chat_settings_kwargs or ChatSettings(
            max_size_kb=400,
            auto_compress=True,
            include_thumbnail=True,
            include_metadata=True
        )
    
    defaults = {
        'display_mode': DisplayMode.CHAT,
        'output_targets': [OutputTarget.CHAT_INLINE],
        'output_format': OutputFormat.BASE64,
        'dpi': 120,  # Good balance of quality and size
        'width': 600,  # Smaller for chat
        'height': 400,
        'chat_settings': chat_settings
    }
    defaults.update(kwargs)
    return ChartConfig(**defaults)


def create_dashboard_config(**kwargs) -> ChartConfig:
    """Create configuration optimized for multi-chart dashboards"""
    defaults = {
        'width': 1200,
        'height': 800,
        'dpi': 120,
        'theme': Theme.CORPORATE,
        'show_legend': True,
        'performance_settings': PerformanceSettings(
            enable_caching=True,
            parallel_processing=True,
            max_workers=4
        )
    }
    defaults.update(kwargs)
    return ChartConfig(**defaults)


def create_high_quality_config(**kwargs) -> ChartConfig:
    """Create configuration for high-quality output (publications, presentations)"""
    defaults = {
        'width': 1600,
        'height': 1200,
        'dpi': 300,
        'output_format': OutputFormat.PDF,
        'theme': Theme.SCIENTIFIC,
        'quality': 100
    }
    defaults.update(kwargs)
    return ChartConfig(**defaults)


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def validate_chart_data_compatibility(chart_data: ChartData, chart_type: ChartType, config: ChartConfig) -> List[str]:
    """Validate that chart data is compatible with chart type and configuration"""
    
    warnings = []
    
    # Check required fields
    required_fields = chart_type.required_fields
    for field in required_fields:
        if not getattr(chart_data, field):
            warnings.append(f"Chart type '{chart_type.value}' requires '{field}' but it's not set")
    
    # Check data size vs performance settings
    if hasattr(chart_data.data, '__len__'):
        data_size = len(chart_data.data)
        if data_size > config.validation_settings.max_data_points:
            warnings.append(f"Data size ({data_size}) exceeds recommended maximum ({config.validation_settings.max_data_points})")
    
    # Check field existence in data
    available_fields = chart_data._get_available_fields()
    for field_name in ['x_field', 'y_field', 'category_field', 'value_field']:
        field_value = getattr(chart_data, field_name)
        if field_value and field_value not in available_fields:
            warnings.append(f"Field '{field_value}' not found in data")
    
    return warnings


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_config() -> ChartConfig:
    """Get default configuration for current environment"""
    return ChartConfig()


def merge_configs(base_config: ChartConfig, *override_configs: ChartConfig) -> ChartConfig:
    """Merge multiple configurations, with later configs taking precedence"""
    result = base_config.clone()
    
    for config in override_configs:
        if config.width != 800:  # Not default
            result.width = config.width
        if config.height != 600:  # Not default
            result.height = config.height
        if config.title:
            result.title = config.title
        # ... continue for other fields as needed
    
    return result
