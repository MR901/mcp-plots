"""
Centralized field validation system for chart generation.

This module provides comprehensive validation for chart data fields,
ensuring that all required fields are present and valid before chart
generation begins. This prevents None errors and provides clear,
actionable error messages.
"""

from typing import Set, List, Dict, Any, Union
import pandas as pd

from .chart_config import ChartData, ChartType
from ..domain.exceptions import (
    DataValidationError, EmptyDataError, MissingFieldError, 
    FieldNotFoundError, InvalidDataFormatError
)


# Keep old exception for backward compatibility
class FieldValidationError(DataValidationError):
    """Legacy exception - use specific exceptions instead."""
    pass


class FieldValidator:
    """
    Centralized validator for chart data fields.
    
    Provides comprehensive validation of field mappings and data columns
    before chart generation, preventing None errors and providing clear
    error messages.
    """
    
    @staticmethod
    def validate_chart_fields(chart_type: ChartType, chart_data: ChartData) -> None:
        """
        Validate that all required fields are present and valid for the chart type.
        
        Args:
            chart_type: The type of chart being generated
            chart_data: The chart data with field mappings
            
        Raises:
            FieldValidationError: If validation fails with detailed error message
        """
        # Get required fields for this chart type
        required_fields = chart_type.required_fields
        
        if not required_fields:
            return  # No validation needed for charts with no required fields
        
        # Check that all required fields are mapped
        missing_fields = []
        for field_name in required_fields:
            field_value = getattr(chart_data, field_name, None)
            if not field_value:
                missing_fields.append(field_name)
        
        if missing_fields:
            raise MissingFieldError(missing_fields, chart_type.value)
        
        # Validate that mapped fields exist in the data
        df = FieldValidator._prepare_dataframe(chart_data.data)
        missing_columns = []
        
        for field_name in required_fields:
            field_value = getattr(chart_data, field_name)
            if field_value and field_value not in df.columns:
                missing_columns.append(f"{field_name}='{field_value}'")
        
        if missing_columns:
            # Parse missing columns back to field mappings dict
            missing_mappings = {}
            for col_str in missing_columns:
                if "=" in col_str:
                    field, mapping = col_str.split("=", 1)
                    missing_mappings[field] = mapping.strip("'\"")
            
            raise FieldNotFoundError(missing_mappings, df.columns.tolist())
    
    @staticmethod
    def validate_optional_fields(chart_data: ChartData, *field_names: str) -> Dict[str, bool]:
        """
        Validate optional fields and return which ones are available.
        
        Args:
            chart_data: The chart data with field mappings
            *field_names: Names of optional fields to check
            
        Returns:
            Dict mapping field names to availability (True/False)
        """
        df = FieldValidator._prepare_dataframe(chart_data.data)
        availability = {}
        
        for field_name in field_names:
            field_value = getattr(chart_data, field_name, None)
            availability[field_name] = (
                field_value is not None and 
                field_value in df.columns
            )
        
        return availability
    
    @staticmethod
    def get_safe_field_value(chart_data: ChartData, field_name: str, default: Any = None) -> Any:
        """
        Safely get a field value, returning default if field is None or missing.
        
        Args:
            chart_data: The chart data with field mappings
            field_name: Name of the field to get
            default: Default value if field is None or missing
            
        Returns:
            Field value or default
        """
        field_value = getattr(chart_data, field_name, None)
        if not field_value:
            return default
        
        df = FieldValidator._prepare_dataframe(chart_data.data)
        if field_value not in df.columns:
            return default
        
        return field_value
    
    @staticmethod
    def _prepare_dataframe(data: Union[List[Dict[str, Any]], pd.DataFrame]) -> pd.DataFrame:
        """Convert data to pandas DataFrame for validation."""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError("Data must be a list of dictionaries or pandas DataFrame")
    
    @staticmethod
    def validate_data_not_empty(data: Union[List[Dict[str, Any]], pd.DataFrame]) -> None:
        """
        Validate that the data is not empty.
        
        Args:
            data: The data to validate
            
        Raises:
            FieldValidationError: If data is empty
        """
        if isinstance(data, list):
            if not data:
                raise EmptyDataError("data")
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                raise EmptyDataError("data")
        else:
            raise InvalidDataFormatError("a pandas DataFrame or list of dictionaries", type(data).__name__)
    
    @staticmethod
    def get_chart_type_help(chart_type: ChartType) -> str:
        """
        Get helpful information about required fields for a chart type.
        
        Args:
            chart_type: The chart type to get help for
            
        Returns:
            Helpful message about required fields
        """
        required_fields = chart_type.required_fields
        if not required_fields:
            return f"{chart_type.value.title()} chart has no required field mappings."
        
        field_list = ", ".join(required_fields)
        return f"{chart_type.value.title()} chart requires: {field_list}"
