"""
Custom Exception Hierarchy

Defines specific exceptions for the MCP Plots Server to provide
clear, actionable error messages and proper error categorization.

This replaces generic ValueError and Exception usage with specific,
meaningful exceptions that can be handled appropriately.
"""

from typing import Dict, Any, Optional, List


class MCPPlotsError(Exception):
    """
    Base exception for all MCP Plots Server errors.
    
    Provides common functionality for all custom exceptions including
    error codes, user-friendly messages, and metadata.
    """
    
    def __init__(self, message: str, error_code: str = None, metadata: Dict[str, Any] = None):
        """
        Initialize base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            metadata: Additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format for API responses."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "error_type": self.__class__.__name__,
            "metadata": self.metadata
        }
    
    def to_mcp_error(self) -> Dict[str, Any]:
        """Convert to MCP-compatible error format."""
        return {
            "status": "error",
            "error": self.message,
            "error_code": self.error_code
        }


# Configuration-related exceptions
class ConfigurationError(MCPPlotsError):
    """Base class for configuration-related errors."""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration values are invalid."""
    
    def __init__(self, field_name: str, value: Any, valid_options: List[str] = None):
        valid_opts = f". Valid options: {', '.join(valid_options)}" if valid_options else ""
        message = f"Invalid {field_name}: '{value}'{valid_opts}"
        super().__init__(
            message=message,
            error_code="INVALID_CONFIG",
            metadata={
                "field_name": field_name,
                "invalid_value": str(value),
                "valid_options": valid_options
            }
        )


class ConfigurationFileError(ConfigurationError):
    """Raised when configuration file operations fail."""
    
    def __init__(self, file_path: str, operation: str, underlying_error: str = None):
        message = f"Configuration file {operation} failed: {file_path}"
        if underlying_error:
            message += f" - {underlying_error}"
        
        super().__init__(
            message=message,
            error_code="CONFIG_FILE_ERROR",
            metadata={
                "file_path": file_path,
                "operation": operation,
                "underlying_error": underlying_error
            }
        )


# Data validation exceptions
class DataValidationError(MCPPlotsError):
    """Base class for data validation errors."""
    pass


class EmptyDataError(DataValidationError):
    """Raised when required data is empty or missing."""
    
    def __init__(self, data_type: str = "data"):
        message = f"{data_type.capitalize()} cannot be empty"
        super().__init__(
            message=message,
            error_code="EMPTY_DATA",
            metadata={"data_type": data_type}
        )


class InvalidDataFormatError(DataValidationError):
    """Raised when data format is incorrect."""
    
    def __init__(self, expected_format: str, received_format: str = None):
        message = f"Data must be {expected_format}"
        if received_format:
            message += f", received {received_format}"
        
        super().__init__(
            message=message,
            error_code="INVALID_DATA_FORMAT",
            metadata={
                "expected_format": expected_format,
                "received_format": received_format
            }
        )


class MissingFieldError(DataValidationError):
    """Raised when required fields are missing."""
    
    def __init__(self, missing_fields: List[str], chart_type: str = None):
        if len(missing_fields) == 1:
            message = f"Missing required field: {missing_fields[0]}"
        else:
            message = f"Missing required fields: {', '.join(missing_fields)}"
        
        if chart_type:
            message += f" for {chart_type} chart"
        
        super().__init__(
            message=message,
            error_code="MISSING_FIELDS",
            metadata={
                "missing_fields": missing_fields,
                "chart_type": chart_type
            }
        )


class FieldNotFoundError(DataValidationError):
    """Raised when mapped fields don't exist in data."""
    
    def __init__(self, field_mappings: Dict[str, str], available_columns: List[str]):
        missing_mappings = [f"{field}='{mapping}'" for field, mapping in field_mappings.items()]
        message = f"Mapped fields not found in data: {', '.join(missing_mappings)}. Available columns: {', '.join(available_columns)}"
        
        super().__init__(
            message=message,
            error_code="FIELD_NOT_FOUND",
            metadata={
                "missing_mappings": field_mappings,
                "available_columns": available_columns
            }
        )


# Chart generation exceptions
class ChartGenerationError(MCPPlotsError):
    """Base class for chart generation errors."""
    pass


class UnsupportedChartTypeError(ChartGenerationError):
    """Raised when chart type is not supported."""
    
    def __init__(self, chart_type: str, supported_types: List[str] = None):
        message = f"Unsupported chart type: {chart_type}"
        if supported_types:
            message += f". Supported types: {', '.join(supported_types)}"
        
        super().__init__(
            message=message,
            error_code="UNSUPPORTED_CHART_TYPE",
            metadata={
                "chart_type": chart_type,
                "supported_types": supported_types
            }
        )


class ChartRenderingError(ChartGenerationError):
    """Raised when chart rendering fails."""
    
    def __init__(self, chart_type: str, underlying_error: str = None):
        message = f"Failed to render {chart_type} chart"
        if underlying_error:
            message += f": {underlying_error}"
        
        super().__init__(
            message=message,
            error_code="CHART_RENDERING_FAILED",
            metadata={
                "chart_type": chart_type,
                "underlying_error": underlying_error
            }
        )


class InvalidChartConfigurationError(ChartGenerationError):
    """Raised when chart configuration is invalid."""
    
    def __init__(self, config_field: str, value: Any, constraint: str = None):
        message = f"Invalid chart configuration: {config_field} = {value}"
        if constraint:
            message += f" ({constraint})"
        
        super().__init__(
            message=message,
            error_code="INVALID_CHART_CONFIG",
            metadata={
                "config_field": config_field,
                "value": str(value),
                "constraint": constraint
            }
        )


# Service-level exceptions
class ServiceError(MCPPlotsError):
    """Base class for service-level errors."""
    pass


class ServiceInitializationError(ServiceError):
    """Raised when service initialization fails."""
    
    def __init__(self, service_name: str, underlying_error: str = None):
        message = f"Failed to initialize {service_name}"
        if underlying_error:
            message += f": {underlying_error}"
        
        super().__init__(
            message=message,
            error_code="SERVICE_INIT_FAILED",
            metadata={
                "service_name": service_name,
                "underlying_error": underlying_error
            }
        )


class ServiceOperationError(ServiceError):
    """Raised when service operation fails."""
    
    def __init__(self, service_name: str, operation: str, underlying_error: str = None):
        message = f"{service_name} {operation} failed"
        if underlying_error:
            message += f": {underlying_error}"
        
        super().__init__(
            message=message,
            error_code="SERVICE_OPERATION_FAILED",
            metadata={
                "service_name": service_name,
                "operation": operation,
                "underlying_error": underlying_error
            }
        )


# Request processing exceptions
class RequestProcessingError(MCPPlotsError):
    """Base class for request processing errors."""
    pass


class InvalidRequestError(RequestProcessingError):
    """Raised when request format or content is invalid."""
    
    def __init__(self, request_type: str, validation_error: str):
        message = f"Invalid {request_type} request: {validation_error}"
        
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST",
            metadata={
                "request_type": request_type,
                "validation_error": validation_error
            }
        )


class RequestTimeoutError(RequestProcessingError):
    """Raised when request processing times out."""
    
    def __init__(self, timeout_seconds: float, operation: str = None):
        message = f"Request timed out after {timeout_seconds}s"
        if operation:
            message += f" during {operation}"
        
        super().__init__(
            message=message,
            error_code="REQUEST_TIMEOUT",
            metadata={
                "timeout_seconds": timeout_seconds,
                "operation": operation
            }
        )


# Utility functions for error handling
def convert_generic_exception(exc: Exception, context: str = None) -> MCPPlotsError:
    """
    Convert generic exceptions to specific MCPPlotsError types.
    
    Args:
        exc: Generic exception to convert
        context: Additional context about where the error occurred
        
    Returns:
        MCPPlotsError: Specific exception type
    """
    error_message = str(exc)
    
    # Map common patterns to specific exceptions
    if "empty" in error_message.lower() or "no data" in error_message.lower():
        return EmptyDataError()
    
    if "field" in error_message.lower() and ("missing" in error_message.lower() or "required" in error_message.lower()):
        return MissingFieldError(["unknown"], context)
    
    if "unsupported" in error_message.lower() or "not supported" in error_message.lower():
        return UnsupportedChartTypeError("unknown")
    
    if "invalid" in error_message.lower():
        return InvalidRequestError(context or "unknown", error_message)
    
    # Default to generic service error
    return ServiceOperationError(
        service_name=context or "unknown",
        operation="operation",
        underlying_error=error_message
    )


def handle_exception_chain(exc: Exception, context: str = None) -> MCPPlotsError:
    """
    Handle exception chains by finding the root cause.
    
    Args:
        exc: Exception (potentially with __cause__ chain)
        context: Context where the error occurred
        
    Returns:
        MCPPlotsError: Appropriate exception type
    """
    # If it's already our custom exception, return as-is
    if isinstance(exc, MCPPlotsError):
        return exc
    
    # Check for chained exceptions
    root_cause = exc
    while root_cause.__cause__ is not None:
        root_cause = root_cause.__cause__
    
    # Convert the root cause
    return convert_generic_exception(root_cause, context)


class ErrorHandler:
    """
    Centralized error handler for consistent error processing.
    
    Provides methods to handle different types of errors and convert
    them to appropriate responses.
    """
    
    @staticmethod
    def handle_service_error(exc: Exception, service_name: str, operation: str) -> Dict[str, Any]:
        """Handle service-level errors."""
        if isinstance(exc, MCPPlotsError):
            return exc.to_mcp_error()
        
        converted = ServiceOperationError(
            service_name=service_name,
            operation=operation,
            underlying_error=str(exc)
        )
        return converted.to_mcp_error()
    
    @staticmethod
    def handle_validation_error(exc: Exception, data_context: str = None) -> Dict[str, Any]:
        """Handle data validation errors."""
        if isinstance(exc, DataValidationError):
            return exc.to_mcp_error()
        
        converted = convert_generic_exception(exc, data_context)
        return converted.to_mcp_error()
    
    @staticmethod
    def handle_chart_error(exc: Exception, chart_type: str = None) -> Dict[str, Any]:
        """Handle chart generation errors."""
        if isinstance(exc, ChartGenerationError):
            return exc.to_mcp_error()
        
        converted = ChartRenderingError(
            chart_type=chart_type or "unknown",
            underlying_error=str(exc)
        )
        return converted.to_mcp_error()
    
    @staticmethod
    def handle_generic_error(exc: Exception, context: str = None) -> Dict[str, Any]:
        """Handle any generic error."""
        if isinstance(exc, MCPPlotsError):
            return exc.to_mcp_error()
        
        converted = convert_generic_exception(exc, context)
        return converted.to_mcp_error()
