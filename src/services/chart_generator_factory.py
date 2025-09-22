"""
Chart Generator Factory

Implements the Factory pattern to eliminate the if/elif chain in chart generation
and provide extensible chart type registration.

This factory replaces the monolithic chart generation dispatch with a clean,
extensible registry pattern that follows the Open/Closed principle.
"""

import logging
from typing import Dict, Type, Callable, Any, Optional, Union, List
from abc import ABC, abstractmethod

from ..visualization.chart_config import ChartData, ChartConfig, ChartType
from ..visualization.constants import ChartConstants


logger = logging.getLogger(__name__)


class ChartGeneratorInterface(ABC):
    """
    Interface for chart generators.
    
    All chart generators must implement this interface to be registered
    with the factory.
    """
    
    @abstractmethod
    def generate(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Any:
        """
        Generate a chart from the given data and configuration.
        
        Args:
            chart_data: Chart data with field mappings
            config: Chart configuration
            **kwargs: Additional options
            
        Returns:
            Chart result (string, bytes, or dict)
        """
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Get list of required field names for this chart type.
        
        Returns:
            List of required field names
        """
        pass
    
    @abstractmethod
    def validate_data(self, chart_data: ChartData) -> None:
        """
        Validate that chart_data is compatible with this generator.
        
        Args:
            chart_data: Chart data to validate
            
        Raises:
            ValueError: If data is invalid for this chart type
        """
        pass


class BaseChartGenerator(ChartGeneratorInterface):
    """
    Base implementation of ChartGeneratorInterface with common functionality.
    
    Provides default implementations for validation and field checking.
    """
    
    def __init__(self, chart_type: str):
        self.chart_type = chart_type
        self._logger = logging.getLogger(f"{__name__}.{chart_type}")
    
    def validate_data(self, chart_data: ChartData) -> None:
        """Default validation implementation."""
        from ..visualization.field_validator import FieldValidator
        
        # Use existing field validator
        FieldValidator.validate_data_not_empty(chart_data.data)
        
        # Validate required fields for this chart type
        try:
            chart_type_enum = ChartType(self.chart_type)
            FieldValidator.validate_chart_fields(chart_type_enum, chart_data)
        except ValueError as e:
            # Chart type not in enum, skip enum-based validation
            self._logger.debug(f"Chart type {self.chart_type} not in ChartType enum, using custom validation")
            self._validate_required_fields(chart_data)
    
    def _validate_required_fields(self, chart_data: ChartData) -> None:
        """Validate required fields for this specific generator."""
        required_fields = self.get_required_fields()
        missing_fields = []
        
        for field_name in required_fields:
            if not getattr(chart_data, field_name, None):
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(
                f"{self.chart_type.capitalize()} chart requires "
                f"{', '.join(missing_fields)}. Please provide these field mappings."
            )
    
    def get_required_fields(self) -> List[str]:
        """Default implementation - override in subclasses."""
        return []


class LegacyChartGeneratorAdapter(BaseChartGenerator):
    """
    Adapter to wrap existing ChartGenerator static methods.
    
    This allows us to use the existing chart generation methods
    within the new factory pattern without rewriting them.
    """
    
    def __init__(self, chart_type: str, generator_method: Callable, required_fields: List[str]):
        super().__init__(chart_type)
        self.generator_method = generator_method
        self.required_fields = required_fields
    
    def generate(self, chart_data: ChartData, config: ChartConfig, **kwargs) -> Any:
        """Generate chart using the legacy method."""
        return self.generator_method(chart_data, config, **kwargs)
    
    def get_required_fields(self) -> List[str]:
        """Return required fields for this chart type."""
        return self.required_fields


class ChartGeneratorFactory:
    """
    Factory for creating and managing chart generators.
    
    Implements the Factory pattern with registration capabilities,
    replacing the if/elif chain in ChartGenerator.run with a clean
    registry lookup.
    """
    
    def __init__(self):
        self._generators: Dict[str, ChartGeneratorInterface] = {}
        self._logger = logging.getLogger(__name__)
        self._register_default_generators()
    
    def register_generator(self, chart_type: str, generator: ChartGeneratorInterface) -> None:
        """
        Register a chart generator for a specific chart type.
        
        Args:
            chart_type: Chart type identifier (e.g., "line", "bar")
            generator: Generator instance implementing ChartGeneratorInterface
        """
        self._generators[chart_type.lower()] = generator
        self._logger.info(f"Registered generator for chart type: {chart_type}")
    
    def unregister_generator(self, chart_type: str) -> None:
        """
        Unregister a chart generator.
        
        Args:
            chart_type: Chart type to unregister
        """
        chart_type = chart_type.lower()
        if chart_type in self._generators:
            del self._generators[chart_type]
            self._logger.info(f"Unregistered generator for chart type: {chart_type}")
    
    def get_generator(self, chart_type: str) -> Optional[ChartGeneratorInterface]:
        """
        Get generator for a specific chart type.
        
        Args:
            chart_type: Chart type identifier
            
        Returns:
            Generator instance or None if not found
        """
        return self._generators.get(chart_type.lower())
    
    def is_supported(self, chart_type: str) -> bool:
        """
        Check if a chart type is supported.
        
        Args:
            chart_type: Chart type to check
            
        Returns:
            True if supported, False otherwise
        """
        return chart_type.lower() in self._generators
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of all supported chart types.
        
        Returns:
            List of supported chart type names
        """
        return list(self._generators.keys())
    
    def generate_chart(self, chart_type: str, chart_data: ChartData, config: ChartConfig, **kwargs) -> Any:
        """
        Generate a chart using the appropriate generator.
        
        Args:
            chart_type: Type of chart to generate
            chart_data: Chart data with field mappings
            config: Chart configuration
            **kwargs: Additional options
            
        Returns:
            Generated chart result
            
        Raises:
            ValueError: If chart type is not supported
        """
        generator = self.get_generator(chart_type)
        if generator is None:
            supported_types = ", ".join(self.get_supported_types())
            raise ValueError(f"Unsupported chart type: {chart_type}. Supported types: {supported_types}")
        
        # Validate data using the generator
        generator.validate_data(chart_data)
        
        # Generate chart
        self._logger.debug(f"Generating {chart_type} chart with generator {generator.__class__.__name__}")
        result = generator.generate(chart_data, config, **kwargs)
        
        return result
    
    def _register_default_generators(self) -> None:
        """Register default generators using the legacy adapter pattern."""
        # Import the existing generator methods
        from ..visualization.generator import ChartGenerator
        
        # Register all chart types with their corresponding methods and required fields
        chart_configs = [
            ("line", ChartGenerator.generate_line_chart, ["x_field", "y_field"]),
            ("bar", ChartGenerator.generate_bar_chart, ["category_field", "value_field"]),
            ("pie", ChartGenerator.generate_pie_chart, ["category_field", "value_field"]),
            ("scatter", ChartGenerator.generate_scatter_chart, ["x_field", "y_field"]),
            ("heatmap", ChartGenerator.generate_heatmap_chart, ["x_field", "y_field", "value_field"]),
            ("area", ChartGenerator.generate_line_chart, ["x_field", "y_field"]),  # Area uses line chart with show_area=True
            ("boxplot", ChartGenerator.generate_boxplot_chart, ["category_field", "value_field"]),
            ("histogram", ChartGenerator.generate_histogram_chart, ["value_field"]),
            ("funnel", ChartGenerator.generate_funnel_chart, ["category_field", "value_field"]),
            ("gauge", ChartGenerator.generate_gauge_chart, ["value_field"]),
            ("radar", ChartGenerator.generate_radar_chart, ["category_field", "value_field"]),
            ("sankey", ChartGenerator.generate_sankey_chart, ["source_field", "target_field", "value_field"]),
        ]
        
        for chart_type, method, required_fields in chart_configs:
            try:
                adapter = LegacyChartGeneratorAdapter(chart_type, method, required_fields)
                self.register_generator(chart_type, adapter)
            except AttributeError as e:
                self._logger.warning(f"Could not register {chart_type} generator: {e}")
    
    def get_factory_info(self) -> Dict[str, Any]:
        """
        Get factory information for debugging.
        
        Returns:
            Dictionary with factory status information
        """
        return {
            "total_generators": len(self._generators),
            "supported_types": self.get_supported_types(),
            "generator_classes": {
                chart_type: generator.__class__.__name__ 
                for chart_type, generator in self._generators.items()
            }
        }


# Global factory instance
_chart_factory: Optional[ChartGeneratorFactory] = None


def get_chart_factory() -> ChartGeneratorFactory:
    """
    Get or create the global chart factory instance.
    
    Returns:
        ChartGeneratorFactory instance
    """
    global _chart_factory
    if _chart_factory is None:
        _chart_factory = ChartGeneratorFactory()
    return _chart_factory


def reset_chart_factory() -> None:
    """Reset the global chart factory (useful for testing)."""
    global _chart_factory
    _chart_factory = None
