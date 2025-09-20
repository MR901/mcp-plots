

import base64
import hashlib
import io
import logging
import threading
import time
import weakref
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable, Type
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.sankey import Sankey

# Import the new configuration system
try:
    from .chart_config import (
        ChartData, ChartConfig, ChartType, Theme, OutputFormat, 
        DisplayMode, OutputTarget, validate_chart_data_compatibility
    )
except ImportError:
    # Fallback for direct execution
    import chart_config
    ChartData = chart_config.ChartData
    ChartConfig = chart_config.ChartConfig
    ChartType = chart_config.ChartType
    Theme = chart_config.Theme
    OutputFormat = chart_config.OutputFormat
    DisplayMode = chart_config.DisplayMode
    OutputTarget = chart_config.OutputTarget
    validate_chart_data_compatibility = chart_config.validate_chart_data_compatibility

try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)



# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ChartGenerationError(Exception):
    """Base exception for chart generation errors"""
    pass

class DataValidationError(ChartGenerationError):
    """Raised when data validation fails"""
    pass

class UnsupportedChartTypeError(ChartGenerationError):
    """Raised when an unsupported chart type is requested"""
    pass

class ConfigurationError(ChartGenerationError):
    """Raised when configuration is invalid"""
    pass

class RenderingError(ChartGenerationError):
    """Raised when chart rendering fails"""
    pass

class CachingError(ChartGenerationError):
    """Raised when caching operations fail"""
    pass


# ============================================================================
# CONFIGURATION AND LIMITS
# ============================================================================

@dataclass
class ChartLimits:
    """Configurable limits for chart generation"""
    max_data_points: int = 50000
    max_series: int = 20
    max_categories: int = 100
    max_colors: int = 50
    max_figure_size_mb: int = 50
    max_cache_entries: int = 1000
    max_concurrent_generations: int = 10
    chart_timeout_seconds: int = 30

@dataclass
class ChartPerformanceSettings:
    """Performance-related settings"""
    enable_caching: bool = True
    enable_parallel_processing: bool = True
    enable_data_sampling: bool = True
    sampling_threshold: int = 10000
    enable_progressive_rendering: bool = False
    memory_efficient_mode: bool = False


# ============================================================================
# CACHING SYSTEM
# ============================================================================

class ChartCache:
    """Thread-safe caching system for generated charts"""
    
    def __init__(self, max_entries: int = 1000, max_size_mb: int = 100):
        self.max_entries = max_entries
        self.max_size_mb = max_size_mb
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._cache_lock = threading.RLock()
        self._current_size_mb = 0.0
    
    def _generate_key(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> str:
        """Generate cache key from chart data and configuration"""
        # Create a hash of the data and configuration
        data_str = str(sorted(chart_data.__dict__.items()))
        config_str = str(sorted(config.__dict__.items()))
        kwargs_str = str(sorted(kwargs.items()))
        
        combined = f"{data_str}#{config_str}#{kwargs_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Optional[Any]:
        """Get cached chart result"""
        key = self._generate_key(chart_data, config, **kwargs)
        
        with self._cache_lock:
            if key in self._cache:
                self._access_times[key] = time.time()
                _logger.debug(f"Cache hit for chart: {key[:8]}...")
                return self._cache[key]['result']
        
        _logger.debug(f"Cache miss for chart: {key[:8]}...")
        return None
    
    def put(self, chart_data: ChartData, config: ChartConfig, result: Any, **kwargs) -> None:
        """Cache chart result"""
        key = self._generate_key(chart_data, config, **kwargs)
        
        # Estimate size
        size_mb = self._estimate_size(result)
        
        with self._cache_lock:
            # Clean cache if necessary
            self._cleanup_if_needed(size_mb)
            
            self._cache[key] = {
                'result': result,
                'size_mb': size_mb,
                'created_at': time.time()
            }
            self._access_times[key] = time.time()
            self._current_size_mb += size_mb
            
            _logger.debug(f"Cached chart: {key[:8]}... ({size_mb:.2f}MB)")
    
    def _estimate_size(self, result: Any) -> float:
        """Estimate memory size of cached result in MB"""
        if isinstance(result, str):
            return len(result.encode()) / (1024 * 1024)
        elif isinstance(result, bytes):
            return len(result) / (1024 * 1024)
        elif hasattr(result, 'getvalue'):
            return len(result.getvalue()) / (1024 * 1024)
        else:
            return 1.0  # Default estimate
    
    def _cleanup_if_needed(self, new_item_size: float) -> None:
        """Clean up cache if limits are exceeded"""
        # Check entry count
        while len(self._cache) >= self.max_entries:
            self._remove_oldest_entry()
        
        # Check size limit
        while (self._current_size_mb + new_item_size) > self.max_size_mb:
            if not self._remove_oldest_entry():
                break  # No more entries to remove
    
    def _remove_oldest_entry(self) -> bool:
        """Remove the oldest accessed entry"""
        if not self._access_times:
            return False
        
        oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        
        if oldest_key in self._cache:
            size_mb = self._cache[oldest_key]['size_mb']
            del self._cache[oldest_key]
            del self._access_times[oldest_key]
            self._current_size_mb -= size_mb
            _logger.debug(f"Evicted cached chart: {oldest_key[:8]}...")
        
        return True
    
    def clear(self) -> None:
        """Clear all cached entries"""
        with self._cache_lock:
            self._cache.clear()
            self._access_times.clear()
            self._current_size_mb = 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._cache_lock:
            return {
                'entries': len(self._cache),
                'size_mb': self._current_size_mb,
                'max_entries': self.max_entries,
                'max_size_mb': self.max_size_mb,
                'hit_ratio': getattr(self, '_hit_ratio', 0.0)
            }


# ============================================================================
# DATA VALIDATION SYSTEM
# ============================================================================

class DataValidator:
    """Comprehensive data validation for chart generation"""
    
    @staticmethod
    def validate_chart_compatibility(chart_data: ChartData, chart_type: ChartType, 
                                   config: ChartConfig, limits: ChartLimits) -> List[str]:
        """Validate data compatibility with chart type and configuration"""
        
        warnings = []
        
        # Use existing validation function
        existing_warnings = validate_chart_data_compatibility(chart_data, chart_type, config)
        warnings.extend(existing_warnings)
        
        # Additional comprehensive validations
        df = DataValidator._get_dataframe(chart_data)
        
        # Data size validation
        if len(df) > limits.max_data_points:
            if config.performance_settings.enable_data_sampling:
                warnings.append(f"Large dataset ({len(df)} points) will be sampled to {limits.max_data_points}")
            else:
                raise DataValidationError(f"Dataset too large: {len(df)} > {limits.max_data_points}")
        
        # Chart-specific validations
        DataValidator._validate_chart_specific_requirements(df, chart_data, chart_type, limits, warnings)
        
        return warnings
    
    @staticmethod
    def _get_dataframe(chart_data: ChartData) -> pd.DataFrame:
        """Convert chart data to DataFrame for validation"""
        if isinstance(chart_data.data, pd.DataFrame):
            return chart_data.data
        elif isinstance(chart_data.data, list):
            return pd.DataFrame(chart_data.data)
        else:
            raise DataValidationError("Data must be a pandas DataFrame or list of dictionaries")
    
    @staticmethod
    def _validate_chart_specific_requirements(df: pd.DataFrame, chart_data: ChartData, 
                                            chart_type: ChartType, limits: ChartLimits, 
                                            warnings: List[str]) -> None:
        """Validate chart-specific data requirements"""
        
        if chart_type == ChartType.SCATTER:
            # Scatter plots need numeric x and y fields
            if chart_data.x_field and chart_data.x_field in df.columns:
                if not pd.api.types.is_numeric_dtype(df[chart_data.x_field]):
                    raise DataValidationError(f"Scatter plot x_field '{chart_data.x_field}' must be numeric")
            
            if chart_data.y_field and chart_data.y_field in df.columns:
                if not pd.api.types.is_numeric_dtype(df[chart_data.y_field]):
                    raise DataValidationError(f"Scatter plot y_field '{chart_data.y_field}' must be numeric")
        
        elif chart_type == ChartType.HEATMAP:
            # Heatmaps need all numeric values
            if chart_data.value_field and chart_data.value_field in df.columns:
                if not pd.api.types.is_numeric_dtype(df[chart_data.value_field]):
                    raise DataValidationError(f"Heatmap value_field '{chart_data.value_field}' must be numeric")
        
        elif chart_type == ChartType.PIE:
            # Pie charts should have reasonable number of categories
            if chart_data.category_field and chart_data.category_field in df.columns:
                unique_categories = df[chart_data.category_field].nunique()
                if unique_categories > limits.max_categories:
                    warnings.append(f"Too many categories for pie chart ({unique_categories}), consider grouping")
                elif unique_categories < 2:
                    raise DataValidationError("Pie chart needs at least 2 categories")
        
        elif chart_type in [ChartType.LINE, ChartType.AREA]:
            # Time series charts benefit from sorted data
            if chart_data.x_field and chart_data.x_field in df.columns:
                if not df[chart_data.x_field].is_monotonic_increasing:
                    warnings.append("Time series data is not sorted by x-axis, consider sorting for better visualization")
        
        elif chart_type == ChartType.SANKEY:
            # Sankey diagrams need balanced flows
            if all(field in df.columns for field in [chart_data.source_field, chart_data.target_field, chart_data.value_field]):
                # Check for negative values
                if (df[chart_data.value_field] < 0).any():
                    raise DataValidationError("Sankey diagram values must be non-negative")


# ============================================================================
# ABSTRACT BASE CHART GENERATOR
# ============================================================================

class BaseChartGenerator(ABC):
    """Abstract base class for chart generators with common functionality"""
    
    def __init__(self, limits: ChartLimits = None, performance_settings: ChartPerformanceSettings = None):
        self.limits = limits or ChartLimits()
        self.performance_settings = performance_settings or ChartPerformanceSettings()
        self._generation_lock = threading.RLock()
    
    @abstractmethod
    def generate_chart(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Union[str, bytes, io.BytesIO]:
        """Generate chart - must be implemented by subclasses"""
        pass
    
    def _setup_theme(self, theme: Theme) -> None:
        """Setup matplotlib theme - common functionality"""
        with self._generation_lock:
            if theme == Theme.DARK:
                plt.style.use('dark_background')
            elif theme == Theme.SEABORN and sns:
                sns.set_style("whitegrid")
            else:
                plt.style.use('default')
    
    def _get_colors(self, theme: Theme, custom_colors: Optional[List[str]] = None, 
                   needed_colors: int = 1) -> List[str]:
        """Get color palette for the theme - improved version"""
        if custom_colors:
            colors = custom_colors
        else:
            colors = theme.color_palette
        
        # Extend colors if needed
        if len(colors) < needed_colors:
            # Cycle through available colors
            extended_colors = []
            for i in range(needed_colors):
                extended_colors.append(colors[i % len(colors)])
            return extended_colors
        
        return colors[:needed_colors]
    
    def _prepare_data(self, chart_data: ChartData, config: ChartConfig) -> pd.DataFrame:
        """Convert data to pandas DataFrame with optional sampling"""
        df = DataValidator._get_dataframe(chart_data)
        
        # Apply data sampling if enabled and data is large
        if (self.performance_settings.enable_data_sampling and 
            len(df) > self.performance_settings.sampling_threshold):
            
            sample_size = min(self.limits.max_data_points, len(df))
            df = df.sample(n=sample_size, random_state=42)
            _logger.info(f"Sampled data from {len(chart_data.data)} to {len(df)} points")
        
        return df
    
    def _save_chart(self, fig: plt.Figure, config: ChartConfig) -> Union[str, bytes, io.BytesIO, Dict[str, Any]]:
        """Save chart in the specified format - enhanced version"""
        try:
            if config.output_format == OutputFormat.BASE64:
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                
                # Check size limits
                size_mb = len(buffer.getvalue()) / (1024 * 1024)
                if size_mb > self.limits.max_figure_size_mb:
                    _logger.warning(f"Generated chart is large ({size_mb:.1f}MB)")
                
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                buffer.close()
                return f"data:image/png;base64,{image_base64}"
            
            elif config.output_format == OutputFormat.MCP_IMAGE:
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                buffer.close()
                return {
                    "content": [
                        {
                            "type": "image",
                            "data": image_base64,
                            "mimeType": "image/png"
                        }
                    ]
                }
            
            elif config.output_format == OutputFormat.MCP_TEXT:
                buffer = io.BytesIO()
                fig.savefig(buffer, format='svg', dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                svg_string = buffer.getvalue().decode('utf-8')
                buffer.close()
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": svg_string
                        }
                    ]
                }
            
            elif config.output_format == OutputFormat.BUFFER:
                buffer = io.BytesIO()
                format_str = 'png' if config.output_format == OutputFormat.PNG else 'svg'
                fig.savefig(buffer, format=format_str, dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                return buffer
            
            else:  # PNG, SVG, PDF
                buffer = io.BytesIO()
                format_str = config.output_format.value
                fig.savefig(buffer, format=format_str, dpi=config.dpi, bbox_inches='tight')
                buffer.seek(0)
                return buffer.getvalue()
                
        except Exception as e:
            raise RenderingError(f"Failed to save chart in {config.output_format.value} format: {str(e)}")
    
    def _apply_common_styling(self, ax, config: ChartConfig) -> None:
        """Apply common styling to chart - reduces duplication"""
        if config.title:
            ax.set_title(config.title, fontsize=14, fontweight='bold')
        if config.x_title:
            ax.set_xlabel(config.x_title)
        if config.y_title:
            ax.set_ylabel(config.y_title)
        
        if config.show_grid:
            ax.grid(True, alpha=config.grid_alpha)
    
    def _cleanup_figure(self, fig: plt.Figure, config: ChartConfig) -> None:
        """Cleanup figure resources"""
        try:
            plt.tight_layout()
            # Only close if not needed for interactive display
            if not config.supports_interactivity():
                plt.close(fig)
        except Exception as e:
            _logger.debug(f"Figure cleanup warning: {e}")


# ============================================================================
# ENHANCED CHART GENERATORS
# ============================================================================

class LineChartGenerator(BaseChartGenerator):
    """Enhanced line chart generator"""
    
    def generate_chart(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Union[str, bytes, io.BytesIO]:
        """Generate line chart with enhanced features"""
        
        # Extract parameters
        smooth = kwargs.get('smooth', False)
        show_area = kwargs.get('show_area', False)
        show_points = kwargs.get('show_points', True)
        stack = kwargs.get('stack', False)
        
        self._setup_theme(config.theme)
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        try:
            df = self._prepare_data(chart_data, config)
            
            # Determine number of series for color allocation
            n_series = 1
            if chart_data.group_field and chart_data.group_field in df.columns:
                n_series = df[chart_data.group_field].nunique()
                n_series = min(n_series, self.limits.max_series)  # Limit series count
            
            colors = self._get_colors(config.theme, config.colors, n_series)
            
            if chart_data.group_field and chart_data.group_field in df.columns:
                # Multiple series with improved handling
                groups = df[chart_data.group_field].unique()[:self.limits.max_series]
                bottom = None if not stack else np.zeros(len(df[chart_data.x_field].unique()))
                
                for i, group in enumerate(groups):
                    group_data = df[df[chart_data.group_field] == group]
                    x_data = group_data[chart_data.x_field]
                    y_data = group_data[chart_data.y_field]
                    
                    color = colors[i % len(colors)]
                    
                    if show_area:
                        if stack and bottom is not None:
                            ax.fill_between(x_data, bottom, bottom + y_data, alpha=0.7, color=color, label=group)
                            if len(bottom) == len(y_data):
                                bottom += y_data
                        else:
                            ax.fill_between(x_data, 0, y_data, alpha=0.7, color=color, label=group)
                    
                    # Smoothing implementation
                    if smooth and len(x_data) > 3:
                        from scipy.interpolate import make_interp_spline
                        try:
                            x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
                            spl = make_interp_spline(x_data, y_data, k=3)
                            y_smooth = spl(x_smooth)
                            ax.plot(x_smooth, y_smooth, color=color, label=group, linewidth=2)
                        except ImportError:
                            _logger.warning("SciPy not available, using linear interpolation for smoothing")
                            ax.plot(x_data, y_data, '-', color=color, label=group, linewidth=2)
                    else:
                        ax.plot(x_data, y_data, '-', color=color, label=group, 
                               marker='o' if show_points else None, markersize=4)
            else:
                # Single series
                x_data = df[chart_data.x_field]
                y_data = df[chart_data.y_field]
                color = colors[0]
                
                if show_area:
                    ax.fill_between(x_data, 0, y_data, alpha=0.7, color=color)
                
                if smooth and len(x_data) > 3:
                    try:
                        from scipy.interpolate import make_interp_spline
                        x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
                        spl = make_interp_spline(x_data, y_data, k=3)
                        y_smooth = spl(x_smooth)
                        ax.plot(x_smooth, y_smooth, color=color, linewidth=2)
                    except ImportError:
                        ax.plot(x_data, y_data, '-', color=color, linewidth=2)
                else:
                    ax.plot(x_data, y_data, '-', color=color,
                           marker='o' if show_points else None, markersize=4)
            
            # Apply common styling
            self._apply_common_styling(ax, config)
            
            if config.show_legend and chart_data.group_field:
                ax.legend(loc=config.legend_position)
            
            result = self._save_chart(fig, config)
            self._cleanup_figure(fig, config)
            return result
            
        except Exception as e:
            plt.close(fig)
            raise RenderingError(f"Line chart generation failed: {str(e)}")


class BarChartGenerator(BaseChartGenerator):
    """Enhanced bar chart generator"""
    
    def generate_chart(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Union[str, bytes, io.BytesIO]:
        """Generate bar chart with enhanced features"""
        
        horizontal = kwargs.get('horizontal', False)
        stack = kwargs.get('stack', False)
        group = kwargs.get('group', False)
        
        self._setup_theme(config.theme)
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        try:
            df = self._prepare_data(chart_data, config)
            
            # Limit categories for readability
            if chart_data.category_field in df.columns:
                unique_categories = df[chart_data.category_field].nunique()
                if unique_categories > self.limits.max_categories:
                    top_categories = df.groupby(chart_data.category_field)[chart_data.value_field].sum().nlargest(self.limits.max_categories).index
                    df = df[df[chart_data.category_field].isin(top_categories)]
                    _logger.info(f"Limited to top {self.limits.max_categories} categories")
            
            colors = self._get_colors(config.theme, config.colors, len(df))
            
            if chart_data.group_field and chart_data.group_field in df.columns:
                # Multiple series with enhanced handling
                if stack:
                    # Stacked bars with improved layout
                    pivot_df = df.pivot(index=chart_data.category_field, 
                                      columns=chart_data.group_field, 
                                      values=chart_data.value_field).fillna(0)
                    
                    # Limit number of groups
                    if len(pivot_df.columns) > self.limits.max_series:
                        pivot_df = pivot_df.iloc[:, :self.limits.max_series]
                    
                    if horizontal:
                        pivot_df.plot(kind='barh', stacked=True, ax=ax, 
                                     color=colors[:len(pivot_df.columns)], width=0.8)
                    else:
                        pivot_df.plot(kind='bar', stacked=True, ax=ax, 
                                     color=colors[:len(pivot_df.columns)], width=0.8)
                        
                elif group:
                    # Grouped bars with improved layout
                    pivot_df = df.pivot(index=chart_data.category_field,
                                      columns=chart_data.group_field,
                                      values=chart_data.value_field).fillna(0)
                    
                    if len(pivot_df.columns) > self.limits.max_series:
                        pivot_df = pivot_df.iloc[:, :self.limits.max_series]
                    
                    if horizontal:
                        pivot_df.plot(kind='barh', ax=ax, color=colors[:len(pivot_df.columns)], width=0.8)
                    else:
                        pivot_df.plot(kind='bar', ax=ax, color=colors[:len(pivot_df.columns)], width=0.8)
            else:
                # Single series with improved styling
                categories = df[chart_data.category_field]
                values = df[chart_data.value_field]
                
                if horizontal:
                    bars = ax.barh(categories, values, color=colors[0], height=0.6)
                else:
                    bars = ax.bar(categories, values, color=colors[0], width=0.6)
                
                # Add value labels on bars if not too many
                if len(categories) <= 20:
                    for bar, value in zip(bars, values):
                        if horizontal:
                            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, 
                                   f'{value:.1f}', va='center', ha='left' if value >= 0 else 'right')
                        else:
                            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                                   f'{value:.1f}', ha='center', va='bottom' if value >= 0 else 'top')
            
            # Apply common styling
            self._apply_common_styling(ax, config)
            
            if config.show_legend and chart_data.group_field:
                ax.legend(loc=config.legend_position)
            
            # Rotate labels if needed
            if not horizontal and len(df[chart_data.category_field].unique()) > 5:
                plt.xticks(rotation=45, ha='right')
            
            result = self._save_chart(fig, config)
            self._cleanup_figure(fig, config)
            return result
            
        except Exception as e:
            plt.close(fig)
            raise RenderingError(f"Bar chart generation failed: {str(e)}")


# ============================================================================
# ENHANCED MAIN CHART GENERATOR
# ============================================================================

class EnhancedChartGenerator:
    """Enhanced chart generation system with all improvements"""
    
    # Chart type registry for plugin architecture
    _chart_generators: Dict[ChartType, Type[BaseChartGenerator]] = {
        ChartType.LINE: LineChartGenerator,
        ChartType.BAR: BarChartGenerator,
        # Add more generators as they're implemented
    }
    
    def __init__(self, limits: ChartLimits = None, performance_settings: ChartPerformanceSettings = None,
                 enable_caching: bool = True):
        self.limits = limits or ChartLimits()
        self.performance_settings = performance_settings or ChartPerformanceSettings()
        
        # Initialize caching
        self.cache = ChartCache(
            max_entries=self.limits.max_cache_entries,
            max_size_mb=50  # 50MB cache limit
        ) if enable_caching else None
        
        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.limits.max_concurrent_generations,
            thread_name_prefix="ChartGen"
        ) if self.performance_settings.enable_parallel_processing else None
        
        # Statistics tracking
        self.stats = {
            'charts_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_errors': 0,
            'rendering_errors': 0,
            'total_generation_time': 0.0
        }
        self._stats_lock = threading.RLock()
    
    @classmethod
    def register_chart_generator(cls, chart_type: ChartType, generator_class: Type[BaseChartGenerator]):
        """Register a custom chart generator - plugin architecture"""
        cls._chart_generators[chart_type] = generator_class
        _logger.info(f"Registered custom generator for {chart_type.value}")
    
    def generate_chart(self, chart_type: Union[str, ChartType], chart_data: ChartData, 
                      config: ChartConfig, **kwargs) -> Union[str, bytes, io.BytesIO]:
        """Enhanced main chart generation method"""
        
        start_time = time.time()
        
        try:
            # Normalize chart type
            if isinstance(chart_type, str):
                chart_type = ChartType(chart_type.lower())
            
            # Check cache first
            if self.cache and self.performance_settings.enable_caching:
                cached_result = self.cache.get(chart_data, config, chart_type=chart_type, **kwargs)
                if cached_result is not None:
                    self._update_stats('cache_hits', 1)
                    return cached_result
                else:
                    self._update_stats('cache_misses', 1)
            
            # Validate data compatibility
            try:
                warnings = DataValidator.validate_chart_compatibility(
                    chart_data, chart_type, config, self.limits
                )
                for warning in warnings:
                    _logger.warning(f"Data validation warning: {warning}")
                    
            except DataValidationError as e:
                self._update_stats('validation_errors', 1)
                raise
            
            # Get appropriate generator
            if chart_type not in self._chart_generators:
                # Fallback to original implementation for unsupported types
                return self._fallback_to_original(chart_type, chart_data, config, **kwargs)
            
            generator_class = self._chart_generators[chart_type]
            generator = generator_class(self.limits, self.performance_settings)
            
            # Generate chart
            result = generator.generate_chart(chart_data, config, **kwargs)
            
            # Cache result if enabled
            if self.cache and self.performance_settings.enable_caching:
                self.cache.put(chart_data, config, result, chart_type=chart_type, **kwargs)
            
            # Update statistics
            generation_time = time.time() - start_time
            self._update_stats('charts_generated', 1)
            self._update_stats('total_generation_time', generation_time)
            
            _logger.info(f"Generated {chart_type.value} chart in {generation_time:.3f}s")
            return result
            
        except ChartGenerationError:
            self._update_stats('rendering_errors', 1)
            raise
        except Exception as e:
            self._update_stats('rendering_errors', 1)
            raise RenderingError(f"Unexpected error in chart generation: {str(e)}")
    
    def _fallback_to_original(self, chart_type: ChartType, chart_data: ChartData, 
                             config: ChartConfig, **kwargs) -> Union[str, bytes, io.BytesIO]:
        """Fallback to original ChartGenerator for unsupported chart types"""
        from .chart_generator import ChartGenerator
        _logger.info(f"Falling back to original generator for {chart_type.value}")
        return ChartGenerator.run(chart_type, chart_data.data, config, **kwargs)
    
    def _update_stats(self, key: str, value: Union[int, float]):
        """Thread-safe statistics update"""
        with self._stats_lock:
            self.stats[key] += value
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics"""
        with self._stats_lock:
            stats = self.stats.copy()
            
        # Add derived statistics
        if stats['charts_generated'] > 0:
            stats['average_generation_time'] = stats['total_generation_time'] / stats['charts_generated']
        
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['cache_hit_ratio'] = stats['cache_hits'] / total_requests
        
        # Add cache statistics
        if self.cache:
            stats['cache_stats'] = self.cache.get_stats()
        
        return stats
    
    def clear_cache(self):
        """Clear the chart cache"""
        if self.cache:
            self.cache.clear()
            _logger.info("Chart cache cleared")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        if self.cache:
            self.cache.clear()
    
    def __del__(self):
        """Destructor"""
        try:
            self.cleanup()
        except:
            pass


# ============================================================================
# BUILDER PATTERN FOR COMPLEX CONFIGURATIONS
# ============================================================================

class ChartBuilder:
    """Fluent API builder for complex chart configurations"""
    
    def __init__(self, chart_type: Union[str, ChartType]):
        self.chart_type = ChartType(chart_type.lower()) if isinstance(chart_type, str) else chart_type
        self.chart_data = None
        self.config = ChartConfig()
        self.generator_kwargs = {}
        self.generator = None
    
    def with_data(self, data: Union[List[Dict], pd.DataFrame]) -> 'ChartBuilder':
        """Set chart data"""
        self.chart_data = ChartData(data=data)
        return self
    
    def map_fields(self, **field_mappings) -> 'ChartBuilder':
        """Map data fields for chart generation"""
        if not self.chart_data:
            raise ConfigurationError("Data must be set before mapping fields")
        
        for field_name, field_value in field_mappings.items():
            if hasattr(self.chart_data, field_name):
                setattr(self.chart_data, field_name, field_value)
        return self
    
    def with_theme(self, theme: Union[str, Theme]) -> 'ChartBuilder':
        """Set chart theme"""
        self.config.theme = Theme(theme) if isinstance(theme, str) else theme
        return self
    
    def with_size(self, width: int, height: int) -> 'ChartBuilder':
        """Set chart dimensions"""
        self.config.width = width
        self.config.height = height
        return self
    
    def with_title(self, title: str, x_title: str = None, y_title: str = None) -> 'ChartBuilder':
        """Set chart titles"""
        self.config.title = title
        if x_title:
            self.config.x_title = x_title
        if y_title:
            self.config.y_title = y_title
        return self
    
    def with_output(self, format: Union[str, OutputFormat], targets: List[Union[str, OutputTarget]] = None) -> 'ChartBuilder':
        """Set output configuration"""
        self.config.output_format = OutputFormat(format) if isinstance(format, str) else format
        if targets:
            self.config.output_targets = [
                OutputTarget(t) if isinstance(t, str) else t for t in targets
            ]
        return self
    
    def with_generator_options(self, **options) -> 'ChartBuilder':
        """Set generator-specific options"""
        self.generator_kwargs.update(options)
        return self
    
    def with_custom_generator(self, generator: EnhancedChartGenerator) -> 'ChartBuilder':
        """Use custom generator instance"""
        self.generator = generator
        return self
    
    def build(self) -> Union[str, bytes, io.BytesIO]:
        """Build and generate the chart"""
        if not self.chart_data:
            raise ConfigurationError("Chart data is required")
        
        generator = self.generator or EnhancedChartGenerator()
        
        return generator.generate_chart(
            self.chart_type,
            self.chart_data,
            self.config,
            **self.generator_kwargs
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_line_chart(data: Union[List[Dict], pd.DataFrame], x_field: str, y_field: str, 
                     title: str = None, **kwargs) -> Union[str, bytes, io.BytesIO]:
    """Convenience function for creating line charts"""
    return (ChartBuilder(ChartType.LINE)
            .with_data(data)
            .map_fields(x_field=x_field, y_field=y_field)
            .with_title(title)
            .with_generator_options(**kwargs)
            .build())

def create_bar_chart(data: Union[List[Dict], pd.DataFrame], category_field: str, value_field: str,
                    title: str = None, **kwargs) -> Union[str, bytes, io.BytesIO]:
    """Convenience function for creating bar charts"""
    return (ChartBuilder(ChartType.BAR)
            .with_data(data)
            .map_fields(category_field=category_field, value_field=value_field)
            .with_title(title)
            .with_generator_options(**kwargs)
            .build())

# Backward compatibility function
def run(chart_type: Union[str, ChartType], data: Union[List[Dict[str, Any]], pd.DataFrame],
        config: ChartConfig = None, **kwargs) -> Union[str, bytes, io.BytesIO]:
    """Backward compatible function that uses enhanced generator"""
    chart_data = ChartData(data=data)
    
    # Map field parameters
    for field in ['x_field', 'y_field', 'category_field', 'value_field', 'group_field', 'size_field']:
        if field in kwargs:
            setattr(chart_data, field, kwargs[field])
    
    config = config or ChartConfig()
    generator = EnhancedChartGenerator()
    
    return generator.generate_chart(chart_type, chart_data, config, **kwargs)
