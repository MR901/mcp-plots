
import base64
import io
import logging
import math
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from weakref import WeakSet

# Chart configuration imports
try:
    from .chart_config import (
        ChartConfig, ChartData, DisplayMode, OutputTarget, OutputFormat, 
        EnvironmentType, InteractiveSettings, ChatSettings, FileSettings
    )
except ImportError:
    # Fallback for direct execution
    import chart_config
    ChartConfig = chart_config.ChartConfig
    ChartData = chart_config.ChartData
    DisplayMode = chart_config.DisplayMode
    OutputTarget = chart_config.OutputTarget
    OutputFormat = chart_config.OutputFormat
    EnvironmentType = chart_config.EnvironmentType
    InteractiveSettings = chart_config.InteractiveSettings
    ChatSettings = chart_config.ChatSettings
    FileSettings = chart_config.FileSettings

# Visualization libraries with graceful fallbacks
try:
    import matplotlib
    import matplotlib.pyplot as plt
    _matplotlib_available = True
except ImportError:
    matplotlib = None
    plt = None
    _matplotlib_available = False

try:
    import seaborn as sns
    _seaborn_available = True
except ImportError:
    sns = None
    _seaborn_available = False

try:
    import tkinter as tk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _tkinter_available = True
except ImportError:
    tk = None
    FigureCanvasTkAgg = None
    _tkinter_available = False

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from PIL import Image
    _pil_available = True
except ImportError:
    Image = None
    _pil_available = False

# Logging setup
try:
    from foglamp.common import logger
    _logger = logger.setup(__name__, level=logging.INFO)
except:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)



# ============================================================================
# RESULT DATA STRUCTURES
# ============================================================================

class ChartDisplayResult:
    """Result of chart display operations"""
    
    def __init__(self):
        self.success: bool = False
        self.outputs: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.performance: Dict[str, float] = {}
        self.created_at: datetime = datetime.now()
    
    def add_output(self, target: OutputTarget, content: Any, metadata: Dict[str, Any] = None):
        """Add output for a specific target"""
        self.outputs[target.value] = {
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now()
        }
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)
        _logger.error(f"ChartDisplayResult error: {error}")
    
    def add_warning(self, warning: str):
        """Add a warning message"""
        self.warnings.append(warning)
        _logger.warning(f"ChartDisplayResult warning: {warning}")
    
    def get_output(self, target: OutputTarget) -> Optional[Any]:
        """Get output for specific target"""
        return self.outputs.get(target.value, {}).get('content')
    
    def has_output(self, target: OutputTarget) -> bool:
        """Check if output exists for target"""
        return target.value in self.outputs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'success': self.success,
            'outputs': self.outputs,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'performance': self.performance,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# BACKEND MANAGEMENT
# ============================================================================

class BackendManager:
    """Manages matplotlib backend configuration"""
    
    _instance = None
    _backend_configured = False
    _current_backend = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._gui_available = None
            self._backend_preferences = ['Qt5Agg', 'TkAgg', 'Agg']
    
    def configure_backend(self, config: ChartConfig) -> str:
        """Configure matplotlib backend based on configuration and environment"""
        
        if not _matplotlib_available:
            raise RuntimeError("Matplotlib not available")
        
        # Check if we need GUI backend
        needs_gui = config.requires_gui()
        
        # Check if GUI is available
        if self._gui_available is None:
            self._gui_available = self._detect_gui_availability()
        
        # Select appropriate backend
        if needs_gui and self._gui_available:
            backend = self._configure_gui_backend()
        else:
            backend = self._configure_headless_backend()
        
        # Apply styling
        self._apply_styling(config)
        
        return backend
    
    def _detect_gui_availability(self) -> bool:
        """Detect if GUI is available"""
        try:
            # Check for display on Unix systems
            if sys.platform.startswith('linux') and 'DISPLAY' not in os.environ:
                return False
            
            # Try to import GUI libraries
            if _tkinter_available:
                # Test if tkinter can create a window
                root = tk.Tk()
                root.withdraw()  # Hide the window
                root.destroy()
                return True
                
        except Exception as e:
            _logger.debug(f"GUI availability check failed: {e}")
        
        return False
    
    def _configure_gui_backend(self) -> str:
        """Configure GUI backend"""
        for backend in self._backend_preferences[:-1]:  # Exclude 'Agg'
            try:
                matplotlib.use(backend, force=True)
                _logger.info(f"Matplotlib configured with {backend} backend for interactive plots")
                return backend
            except ImportError:
                continue
        
        # Fallback to Agg if no GUI backend available
        return self._configure_headless_backend()
    
    def _configure_headless_backend(self) -> str:
        """Configure headless backend"""
        matplotlib.use('Agg', force=True)
        _logger.info("Using Agg backend for headless plot generation")
        return 'Agg'
    
    def _apply_styling(self, config: ChartConfig):
        """Apply matplotlib styling based on configuration"""
        try:
            # Set style based on theme
            if config.theme.value == 'dark':
                plt.style.use('dark_background')
            elif config.theme.value == 'seaborn' and _seaborn_available:
                sns.set_style("whitegrid")
            else:
                plt.style.use('default')
                
            # Configure interactive mode
            if config.supports_interactivity():
                plt.ion()
                _logger.debug("Matplotlib interactive mode enabled")
            else:
                plt.ioff()
                _logger.debug("Matplotlib interactive mode disabled")
                
        except Exception as e:
            _logger.warning(f"Failed to apply styling: {e}")


# ============================================================================
# INTERACTIVE DISPLAY MANAGEMENT  
# ============================================================================

class InteractiveDisplayManager:
    """Manages interactive plot windows with proper resource management"""
    
    def __init__(self, max_windows: int = 10):
        self.max_windows = max_windows
        self.active_windows: WeakSet = WeakSet()
        self.window_threads: Set[threading.Thread] = set()
        self.thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="PlotWindow")
        
    def show_plot(self, fig, title: str = "Chart", settings: InteractiveSettings = None) -> bool:
        """Show plot in interactive window"""
        
        if not _tkinter_available:
            _logger.error("Tkinter not available for interactive display")
            return False
        
        if settings is None:
            settings = InteractiveSettings()
        
        # Check window limits
        if len(self.active_windows) >= self.max_windows:
            self._cleanup_closed_windows()
            if len(self.active_windows) >= self.max_windows:
                _logger.warning(f"Maximum windows ({self.max_windows}) reached")
                return False
        
        try:
            if settings.non_blocking:
                # Non-blocking display in separate thread
                future = self.thread_pool.submit(self._create_window, fig, title, settings)
                return True
            else:
                # Blocking display in current thread
                return self._create_window(fig, title, settings)
                
        except Exception as e:
            _logger.error(f"Failed to show interactive plot: {e}")
            return False
    
    def _create_window(self, fig, title: str, settings: InteractiveSettings) -> bool:
        """Create and show Tkinter window with matplotlib figure"""
        try:
            root = tk.Tk()
            root.title(settings.window_title or title)
            root.geometry(f"{settings.window_size[0]}x{settings.window_size[1]}")
            
            if settings.always_on_top:
                root.wm_attributes("-topmost", 1)
            
            if not settings.resizable:
                root.resizable(False, False)
            
            # Create matplotlib canvas
            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.draw()
            
            # Add toolbar if requested
            if settings.show_toolbar:
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                toolbar = NavigationToolbar2Tk(canvas, root)
                toolbar.update()
            
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            
            # Setup window closing
            def on_closing():
                try:
                    canvas.get_tk_widget().destroy()
                    root.quit()
                    root.destroy()
                except Exception as e:
                    _logger.debug(f"Window cleanup error: {e}")
            
            root.protocol("WM_DELETE_WINDOW", on_closing)
            
            # Register window for tracking
            self.active_windows.add(root)
            
            # Start main loop
            root.mainloop()
            return True
            
        except Exception as e:
            _logger.error(f"Failed to create interactive window: {e}")
            return False
    
    def _cleanup_closed_windows(self):
        """Clean up references to closed windows"""
        # WeakSet automatically removes dead references
        pass
    
    def close_all_windows(self):
        """Close all active windows"""
        for window in list(self.active_windows):
            try:
                if hasattr(window, 'destroy'):
                    window.destroy()
            except:
                pass
        
        self.active_windows.clear()
    
    def __del__(self):
        """Cleanup resources"""
        try:
            self.thread_pool.shutdown(wait=False)
            self.close_all_windows()
        except:
            pass


# ============================================================================
# CHAT FORMATTING
# ============================================================================

class ChatFormatter:
    """Handles formatting charts for chat interfaces"""
    
    def __init__(self):
        self.compression_cache: Dict[str, bytes] = {}
        self._max_cache_size = 50
    
    def format_for_chat(self, chart_result: Any, config: ChartConfig) -> Dict[str, Any]:
        """Format chart result for chat display with optimization"""
        
        chat_settings = config.chat_settings
        result = {
            'success': False,
            'chat_display': {},
            'metadata': {},
            'performance': {}
        }
        
        start_time = time.time()
        
        try:
            # Extract base64 image data
            base64_image = self._extract_base64_image(chart_result)
            if not base64_image:
                result['error'] = "No image data found in chart result"
                return result
            
            # Calculate original size
            original_size_kb = len(base64_image) * 3 // 4 // 1024
            
            # Compress if needed
            final_image, compressed_size_kb = self._optimize_image_for_chat(
                base64_image, chat_settings.max_size_kb
            )
            
            # Create chat display content
            chart_title = getattr(chart_result, 'title', config.title or 'Chart')
            
            chat_display = {
                'markdown_image': f"![{chart_title}](data:image/png;base64,{final_image})",
                'title': chart_title,
                'description': getattr(chart_result, 'description', 'Data visualization'),
                'image_available': True,
                'original_size_kb': original_size_kb,
                'final_size_kb': compressed_size_kb,
                'compressed': compressed_size_kb < original_size_kb
            }
            
            # Add thumbnail if requested
            if chat_settings.include_thumbnail and compressed_size_kb > 100:
                thumbnail = self._create_thumbnail(final_image, chat_settings.thumbnail_size)
                if thumbnail:
                    chat_display['thumbnail'] = f"data:image/png;base64,{thumbnail}"
            
            # Add metadata if requested
            if chat_settings.include_metadata:
                chat_display['metadata'] = self._extract_metadata(chart_result, config)
            
            # Add data summary if requested
            if chat_settings.show_data_summary:
                chat_display['data_summary'] = self._create_data_summary(chart_result)
            
            result['success'] = True
            result['chat_display'] = chat_display
            result['performance']['format_time_ms'] = (time.time() - start_time) * 1000
            
        except Exception as e:
            result['error'] = f"Failed to format for chat: {str(e)}"
            _logger.error(f"Chat formatting error: {e}")
        
        return result
    
    def _extract_base64_image(self, chart_result: Any) -> Optional[str]:
        """Extract base64 image data from various chart result formats"""
        
        # Handle different result types
        if hasattr(chart_result, 'base64_image'):
            return chart_result.base64_image
        elif isinstance(chart_result, dict):
            return chart_result.get('base64_image')
        elif isinstance(chart_result, str):
            # Assume it's already base64
            return chart_result
        elif hasattr(chart_result, 'getvalue'):
            # BytesIO buffer
            chart_result.seek(0)
            return base64.b64encode(chart_result.getvalue()).decode('utf-8')
        
        return None
    
    def _optimize_image_for_chat(self, base64_image: str, max_size_kb: int) -> Tuple[str, int]:
        """Optimize image size for chat display"""
        
        current_size_kb = len(base64_image) * 3 // 4 // 1024
        
        if current_size_kb <= max_size_kb:
            return base64_image, current_size_kb
        
        if not _pil_available:
            _logger.warning("PIL not available for image compression")
            return base64_image, current_size_kb
        
        try:
            # Decode image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate compression ratio needed
            target_ratio = max_size_kb / current_size_kb
            
            # Resize image to reduce size
            if target_ratio < 1.0:
                scale_factor = math.sqrt(target_ratio * 0.8)  # Leave some margin
                new_size = (
                    int(image.width * scale_factor),
                    int(image.height * scale_factor)
                )
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            buffer = io.BytesIO()
            
            # Try different quality levels
            for quality in [85, 75, 65, 50]:
                buffer.seek(0)
                buffer.truncate(0)
                image.save(buffer, format='PNG', optimize=True)
                
                compressed_data = buffer.getvalue()
                compressed_b64 = base64.b64encode(compressed_data).decode('utf-8')
                compressed_size_kb = len(compressed_b64) * 3 // 4 // 1024
                
                if compressed_size_kb <= max_size_kb:
                    return compressed_b64, compressed_size_kb
            
            # If still too large, return best attempt
            return compressed_b64, compressed_size_kb
            
        except Exception as e:
            _logger.warning(f"Image optimization failed: {e}")
            return base64_image, current_size_kb
    
    def _create_thumbnail(self, base64_image: str, size: Tuple[int, int]) -> Optional[str]:
        """Create thumbnail from base64 image"""
        
        if not _pil_available:
            return None
        
        try:
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            image.save(buffer, format='PNG', optimize=True)
            thumbnail_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return thumbnail_b64
            
        except Exception as e:
            _logger.debug(f"Thumbnail creation failed: {e}")
            return None
    
    def _extract_metadata(self, chart_result: Any, config: ChartConfig) -> Dict[str, Any]:
        """Extract metadata from chart result"""
        
        metadata = {
            'chart_type': getattr(chart_result, 'plot_type', 'unknown'),
            'theme': config.theme.value,
            'dimensions': f"{config.width}x{config.height}",
            'dpi': config.dpi,
            'created_at': datetime.now().isoformat()
        }
        
        # Add result-specific metadata
        if hasattr(chart_result, 'metadata'):
            metadata.update(chart_result.metadata)
        
        return metadata
    
    def _create_data_summary(self, chart_result: Any) -> Dict[str, Any]:
        """Create summary of the underlying data"""
        
        summary = {
            'available': False,
            'message': 'Data summary not available'
        }
        
        try:
            if hasattr(chart_result, 'metadata') and 'datapoints' in chart_result.metadata:
                datapoints = chart_result.metadata['datapoints']
                summary = {
                    'available': True,
                    'datapoint_count': len(datapoints) if isinstance(datapoints, list) else 1,
                    'datapoints': datapoints if isinstance(datapoints, list) else [datapoints]
                }
        
        except Exception as e:
            _logger.debug(f"Data summary creation failed: {e}")
        
        return summary


# ============================================================================
# FILE OUTPUT MANAGER
# ============================================================================

class FileOutputManager:
    """Manages file output operations"""
    
    def __init__(self):
        self.output_cache: Dict[str, Path] = {}
    
    def save_to_file(self, chart_result: Any, config: ChartConfig) -> Dict[str, Any]:
        """Save chart to file based on configuration"""
        
        file_settings = config.file_settings
        result = {
            'success': False,
            'file_path': None,
            'metadata': {}
        }
        
        try:
            # Determine output directory
            output_dir = file_settings.directory or Path.cwd() / "charts"
            
            if file_settings.create_directories:
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = self._generate_filename(chart_result, config)
            file_path = output_dir / filename
            
            # Handle existing file
            if file_path.exists():
                if file_settings.backup_existing:
                    backup_path = file_path.with_suffix(f".backup_{int(time.time())}{file_path.suffix}")
                    file_path.rename(backup_path)
                elif not file_settings.overwrite_existing:
                    if file_settings.auto_increment:
                        file_path = self._get_incremented_path(file_path)
                    else:
                        raise FileExistsError(f"File already exists: {file_path}")
            
            # Save file
            self._write_chart_to_file(chart_result, file_path, config)
            
            result['success'] = True
            result['file_path'] = str(file_path)
            result['metadata'] = {
                'size_bytes': file_path.stat().st_size,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            result['error'] = f"Failed to save file: {str(e)}"
            _logger.error(f"File save error: {e}")
        
        return result
    
    def _generate_filename(self, chart_result: Any, config: ChartConfig) -> str:
        """Generate filename based on template"""
        
        file_settings = config.file_settings
        template = file_settings.filename_template
        
        # Template variables
        variables = {
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'id': config.config_id[:8],
            'title': (config.title or 'chart').replace(' ', '_').lower(),
            'type': getattr(chart_result, 'plot_type', 'chart'),
            'theme': config.theme.value
        }
        
        # Apply template
        filename = template.format(**variables)
        
        # Add extension based on output format
        if config.output_format == OutputFormat.PNG:
            extension = '.png'
        elif config.output_format == OutputFormat.SVG:
            extension = '.svg'
        elif config.output_format == OutputFormat.PDF:
            extension = '.pdf'
        else:
            extension = '.png'  # Default
        
        return filename + extension
    
    def _get_incremented_path(self, base_path: Path) -> Path:
        """Get incremented filename to avoid conflicts"""
        
        counter = 1
        while True:
            stem = base_path.stem
            suffix = base_path.suffix
            new_path = base_path.parent / f"{stem}_{counter}{suffix}"
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            if counter > 1000:  # Prevent infinite loop
                raise RuntimeError("Too many file conflicts")
    
    def _write_chart_to_file(self, chart_result: Any, file_path: Path, config: ChartConfig):
        """Write chart data to file"""
        
        # Handle different chart result types
        if hasattr(chart_result, 'figure'):
            # Matplotlib figure
            chart_result.figure.savefig(
                str(file_path), 
                dpi=config.dpi, 
                bbox_inches='tight',
                facecolor='white' if config.theme.value != 'dark' else 'black'
            )
        elif hasattr(chart_result, 'base64_image'):
            # Base64 image data
            image_data = base64.b64decode(chart_result.base64_image)
            file_path.write_bytes(image_data)
        elif isinstance(chart_result, bytes):
            # Raw bytes
            file_path.write_bytes(chart_result)
        elif hasattr(chart_result, 'getvalue'):
            # BytesIO buffer
            chart_result.seek(0)
            file_path.write_bytes(chart_result.getvalue())
        else:
            raise ValueError(f"Unsupported chart result type: {type(chart_result)}")


# ============================================================================
# MAIN DISPLAY MANAGER
# ============================================================================

class ChartDisplayManager:
    """Unified chart display and output management system"""
    
    def __init__(self, config: ChartConfig = None):
        self.config = config or ChartConfig()
        self.backend_manager = BackendManager()
        self.interactive_manager = InteractiveDisplayManager(
            max_windows=self.config.interactive_settings.max_windows
        )
        self.chat_formatter = ChatFormatter()
        self.file_manager = FileOutputManager()
        
        # Performance tracking
        self.performance_stats = {
            'charts_processed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Configure matplotlib backend
        if _matplotlib_available:
            try:
                self.backend_manager.configure_backend(self.config)
            except Exception as e:
                _logger.warning(f"Backend configuration failed: {e}")
    
    def display_chart(self, chart_result: Any, config: ChartConfig = None) -> ChartDisplayResult:
        """Main entry point for chart display and output generation"""
        
        start_time = time.time()
        effective_config = config or self.config
        result = ChartDisplayResult()
        
        try:
            _logger.info(f"Processing chart display with {len(effective_config.output_targets)} targets")
            
            # Process each output target
            for target in effective_config.output_targets:
                try:
                    if target == OutputTarget.POPUP_WINDOW:
                        success = self._handle_interactive_display(chart_result, effective_config, result)
                        if success:
                            result.add_output(target, "Interactive window opened", {"non_blocking": True})
                    
                    elif target == OutputTarget.CHAT_INLINE:
                        chat_output = self._handle_chat_display(chart_result, effective_config, result)
                        if chat_output.get('success'):
                            result.add_output(target, chat_output['chat_display'])
                    
                    elif target == OutputTarget.FILE:
                        file_output = self._handle_file_output(chart_result, effective_config, result)
                        if file_output.get('success'):
                            result.add_output(target, file_output['file_path'], file_output.get('metadata'))
                    
                    elif target == OutputTarget.MEMORY:
                        result.add_output(target, chart_result, {"stored_in_memory": True})
                    
                    elif target == OutputTarget.API_RESPONSE:
                        api_output = self._handle_api_output(chart_result, effective_config)
                        result.add_output(target, api_output)
                    
                    else:
                        result.add_warning(f"Output target '{target.value}' not implemented")
                
                except Exception as e:
                    result.add_error(f"Failed to process target '{target.value}': {str(e)}")
            
            # Set overall success based on whether we have any outputs
            result.success = len(result.outputs) > 0
            
            # Record performance
            processing_time = time.time() - start_time
            result.performance['total_time_ms'] = processing_time * 1000
            self.performance_stats['charts_processed'] += 1
            self.performance_stats['total_processing_time'] += processing_time
            
            _logger.info(f"Chart display completed in {processing_time:.3f}s with {len(result.outputs)} outputs")
            
        except Exception as e:
            result.add_error(f"Chart display failed: {str(e)}")
            _logger.error(f"Chart display error: {e}")
        
        return result
    
    def _handle_interactive_display(self, chart_result: Any, config: ChartConfig, result: ChartDisplayResult) -> bool:
        """Handle interactive popup window display"""
        
        if not _matplotlib_available or not _tkinter_available:
            result.add_error("Interactive display not available (missing matplotlib or tkinter)")
            return False
        
        try:
            # Extract figure
            fig = None
            if hasattr(chart_result, 'figure'):
                fig = chart_result.figure
            else:
                result.add_error("No matplotlib figure found in chart result")
                return False
            
            title = config.title or getattr(chart_result, 'title', 'Chart')
            
            success = self.interactive_manager.show_plot(
                fig, title, config.interactive_settings
            )
            
            if not success:
                result.add_error("Failed to create interactive window")
            
            return success
            
        except Exception as e:
            result.add_error(f"Interactive display error: {str(e)}")
            return False
    
    def _handle_chat_display(self, chart_result: Any, config: ChartConfig, result: ChartDisplayResult) -> Dict[str, Any]:
        """Handle chat formatting"""
        
        try:
            chat_output = self.chat_formatter.format_for_chat(chart_result, config)
            
            if not chat_output.get('success'):
                result.add_error(f"Chat formatting failed: {chat_output.get('error', 'Unknown error')}")
            
            return chat_output
            
        except Exception as e:
            result.add_error(f"Chat formatting error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_file_output(self, chart_result: Any, config: ChartConfig, result: ChartDisplayResult) -> Dict[str, Any]:
        """Handle file output"""
        
        try:
            file_output = self.file_manager.save_to_file(chart_result, config)
            
            if not file_output.get('success'):
                result.add_error(f"File save failed: {file_output.get('error', 'Unknown error')}")
            
            return file_output
            
        except Exception as e:
            result.add_error(f"File output error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_api_output(self, chart_result: Any, config: ChartConfig) -> Dict[str, Any]:
        """Handle API response formatting"""
        
        try:
            # Create API-friendly output
            api_output = {
                'success': True,
                'chart_data': {},
                'metadata': {
                    'config_id': config.config_id,
                    'created_at': datetime.now().isoformat(),
                    'theme': config.theme.value,
                    'dimensions': {'width': config.width, 'height': config.height}
                }
            }
            
            # Add chart-specific data
            if hasattr(chart_result, 'base64_image'):
                api_output['chart_data']['image'] = chart_result.base64_image
                api_output['chart_data']['format'] = 'base64_png'
            
            if hasattr(chart_result, 'title'):
                api_output['metadata']['title'] = chart_result.title
            
            if hasattr(chart_result, 'description'):
                api_output['metadata']['description'] = chart_result.description
            
            return api_output
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        
        stats = self.performance_stats.copy()
        
        if stats['charts_processed'] > 0:
            stats['average_processing_time'] = stats['total_processing_time'] / stats['charts_processed']
        else:
            stats['average_processing_time'] = 0.0
        
        return stats
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.interactive_manager.close_all_windows()
        except Exception as e:
            _logger.debug(f"Cleanup error: {e}")
    
    def __del__(self):
        """Destructor"""
        self.cleanup()


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_display_manager_for_environment(env_type: EnvironmentType = None) -> ChartDisplayManager:
    """Create display manager optimized for specific environment"""
    
    try:
        from .chart_config import create_config_for_environment
    except ImportError:
        import chart_config
        create_config_for_environment = chart_config.create_config_for_environment
    
    config = create_config_for_environment(env_type)
    return ChartDisplayManager(config)


def create_chat_display_manager() -> ChartDisplayManager:
    """Create display manager optimized for chat interfaces"""
    
    try:
        from .chart_config import create_chat_optimized_config
    except ImportError:
        import chart_config
        create_chat_optimized_config = chart_config.create_chat_optimized_config
    
    config = create_chat_optimized_config()
    return ChartDisplayManager(config)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_chart_for_chat(chart_result: Any, max_size_kb: int = 400) -> Dict[str, Any]:
    """Quick utility function to format chart for chat display"""
    
    try:
        from .chart_config import create_chat_optimized_config
    except ImportError:
        import chart_config
        create_chat_optimized_config = chart_config.create_chat_optimized_config
    
    config = create_chat_optimized_config(
        chat_settings={'max_size_kb': max_size_kb}
    )
    
    formatter = ChatFormatter()
    return formatter.format_for_chat(chart_result, config)


def show_chart_interactive(chart_result: Any, title: str = "Chart") -> bool:
    """Quick utility function to show chart in interactive window"""
    
    try:
        from .chart_config import ChartConfig, DisplayMode, OutputTarget
    except ImportError:
        import chart_config
        ChartConfig = chart_config.ChartConfig
        DisplayMode = chart_config.DisplayMode
        OutputTarget = chart_config.OutputTarget
    
    config = ChartConfig(
        display_mode=DisplayMode.INTERACTIVE,
        output_targets=[OutputTarget.POPUP_WINDOW],
        title=title
    )
    
    manager = ChartDisplayManager(config)
    result = manager.display_chart(chart_result)
    
    return result.success
