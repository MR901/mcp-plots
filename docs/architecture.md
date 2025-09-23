# MCP Plots Server - Architecture Documentation

## Overview

The MCP Plots Server is a sophisticated data visualization system built on a clean, layered architecture following Domain-Driven Design (DDD) principles. This document provides comprehensive technical documentation for developers working with or extending the system.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Presentation Layer                       │
├─────────────────┬─────────────────────┬─────────────────────────┤
│   MCP Tools     │    HTTP Endpoints   │    CLI Interface        │
│ (Cursor, etc.)  │   (Future)          │   (Development)         │
└─────────────────┴─────────────────────┴─────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       Application Layer                          │
├─────────────────────────┬───────────────────────────────────────┤
│   Chart Rendering       │         Configuration                 │
│      Service            │           Service                     │
│                         │                                       │
│ • Request orchestration │ • User preferences                    │
│ • Business logic        │ • Thread-safe caching                │
│ • Response formatting   │ • Atomic file operations              │
└─────────────────────────┴───────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
├─────────────────────────┬───────────────────────────────────────┤
│      Domain Models      │           Exceptions                  │
│                         │                                       │
│ • ChartRequest          │ • Custom error hierarchy             │
│ • ChartResponse         │ • Specific error types               │
│ • UserPreferences       │ • Error handling strategies          │
│ • ChartData             │                                       │
│ • ChartConfig           │                                       │
└─────────────────────────┴───────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                        │
├─────────────────┬─────────────────────┬─────────────────────────┤
│  Chart          │    Visualization    │    External             │
│ Generation      │     Engines         │   Dependencies          │
│                 │                     │                         │
│ • Factory       │ • MermaidGenerator  │ • matplotlib            │
│ • Providers     │ • ChartGenerator    │ • pandas                │
│ • Registry      │ • Field validation  │ • seaborn               │
└─────────────────┴─────────────────────┴─────────────────────────┘
```

## Module Structure

### `/src/app/` - Server Foundation
- **`server.py`**: FastMCP server wrapper and lifecycle management
- **`__main__.py`**: Entry point, configuration, and command-line interface

### `/src/capabilities/` - MCP Protocol Interface
- **`tools.py`**: MCP tool implementations (render_chart, configure_preferences)
- **`prompts.py`**: MCP prompts for enhanced AI interaction

### `/src/domain/` - Core Business Logic
- **`models.py`**: Domain entities and value objects
- **`exceptions.py`**: Custom exception hierarchy with error handling

### `/src/services/` - Application Services
- **`chart_service.py`**: Chart rendering orchestration service
- **`configuration_service.py`**: Thread-safe configuration management
- **`chart_generator_factory.py`**: Factory for chart generation engines

### `/src/visualization/` - Chart Generation Engine
- **`generator.py`**: Matplotlib-based high-fidelity chart generation
- **`mermaid_generator.py`**: Text-based diagram generation (Mermaid syntax)
- **`chart_config.py`**: Configuration classes and enums
- **`field_validator.py`**: Data validation and field mapping
- **`constants.py`**: System constants and configuration defaults

## Key Design Patterns

### 1. **Service Layer Pattern**
Encapsulates business logic in dedicated service classes:
- `ChartRenderingService`: Orchestrates chart generation workflow
- `ConfigurationService`: Manages user preferences and settings

### 2. **Factory Pattern**
`ChartGeneratorFactory` provides flexible chart engine creation:
```python
factory = get_chart_factory()
generator = factory.create_generator(chart_type, output_format)
result = generator.generate(data, config)
```

### 3. **Strategy Pattern**
Different chart types use specialized generation strategies:
- `MermaidGenerator`: Text-based diagrams for universal compatibility
- `ChartGenerator`: High-fidelity matplotlib-based image generation

### 4. **Domain-Driven Design**
- Clear separation between domain logic and infrastructure concerns
- Rich domain models with behavior and validation
- Ubiquitous language throughout the codebase

### 5. **Dependency Injection**
Services receive dependencies through constructor injection:
```python
chart_service = ChartRenderingService(
    config_service=config_service,
    chart_factory=chart_factory
)
```

## Data Flow Architecture

### Request Processing Pipeline

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ MCP Client  │ -> │   MCP Tools     │ -> │ Chart Service   │
│ (Cursor)    │    │ render_chart()  │    │ render_chart()  │
└─────────────┘    └─────────────────┘    └─────────────────┘
                            │                       │
                            v                       v
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ MCP Client  │ <- │   MCP Response  │ <- │ Chart Generator │
│ (Display)   │    │ Content Format  │    │ Factory/Engine  │
└─────────────┘    └─────────────────┘    └─────────────────┘
```

### Configuration Management Flow

```
┌──────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  User Input  │ -> │ Configuration       │ -> │   File System      │
│ (Preferences)│    │ Service             │    │ ~/.plots_mcp_...    │
└──────────────┘    └─────────────────────┘    └─────────────────────┘
                             │                           │
                             v                           v
┌──────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ Chart Config │ <- │  Memory Cache       │ <- │ Atomic File Ops     │
│ (Applied)    │    │ (Thread-Safe)       │    │ (Data Integrity)    │
└──────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Error Handling Strategy

### Custom Exception Hierarchy
```
MCPPlotsError (Base)
├── ConfigurationError
│   ├── InvalidConfigurationError
│   └── ConfigurationFileError
├── DataValidationError
│   ├── EmptyDataError
│   ├── InvalidDataFormatError
│   ├── MissingFieldError
│   └── FieldNotFoundError
├── ChartGenerationError
│   ├── UnsupportedChartTypeError
│   ├── ChartRenderingError
│   └── InvalidChartConfigurationError
└── ServiceError
    ├── ServiceInitializationError
    └── ServiceOperationError
```

### Error Recovery Strategies
1. **Graceful Degradation**: Fallback to simpler chart types when complex ones fail
2. **Default Values**: Use sensible defaults when configuration is invalid
3. **Error Propagation**: Structured error information for debugging
4. **Logging**: Comprehensive logging at appropriate levels

## Thread Safety & Concurrency

### Thread-Safe Components
- **ConfigurationService**: Uses `threading.Lock()` for cache synchronization
- **ChartGenerator**: Stateless static methods, inherently thread-safe
- **MermaidGenerator**: Pure functions with no shared state

### Concurrency Design
- **Stateless Services**: Most operations are stateless for scalability
- **Immutable Data**: Domain objects are designed to be immutable where possible
- **Atomic Operations**: File operations use atomic write patterns

## Performance Optimization

### Memory Management
- **Context Managers**: Automatic resource cleanup for buffers and files
- **Streaming Processing**: Process data without loading entire datasets in memory
- **Resource Pooling**: Efficient reuse of expensive resources (matplotlib figures)

### Caching Strategy
- **User Preferences**: In-memory caching with file-based persistence
- **Chart Templates**: Potential future caching of chart configurations
- **Generated Content**: Optional caching of generated charts (future enhancement)

### Scalability Considerations
- **Horizontal Scaling**: Stateless design enables easy horizontal scaling
- **Resource Limits**: Configurable limits on data size and processing time
- **Async Support**: Architecture ready for async/await enhancement

## Extension Points

### Adding New Chart Types
1. **Define ChartType Enum**: Add new type to `chart_config.py`
2. **Implement Generator**: Add methods to both generators
3. **Update Factory**: Register new type in factory
4. **Add Validation**: Update field requirements

### Custom Output Formats
1. **Define OutputFormat**: Add to enum in `chart_config.py`
2. **Implement Generator**: Add format handling in generators
3. **Update Service**: Add format-specific processing

### New MCP Tools
1. **Define Tool**: Add function to `tools.py`
2. **Add Validation**: Implement input validation
3. **Register Tool**: Use `@mcp_server.tool()` decorator

## Testing Strategy

### Test Categories (Planned)
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Service interaction testing
3. **End-to-End Tests**: Full request/response cycle testing
4. **Performance Tests**: Memory usage and execution time validation

### Test Infrastructure Requirements
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-benchmark**: Performance benchmarking
- **Factory Pattern**: Test data generation

## Monitoring & Observability

### Logging Strategy
- **Structured Logging**: JSON format for machine parsing
- **Log Levels**: DEBUG, INFO, WARN, ERROR with appropriate usage
- **Context**: Request IDs and user context in logs
- **Performance**: Timing information for operations

### Metrics (Future)
- **Chart Generation Counts**: Track usage patterns
- **Error Rates**: Monitor system health
- **Performance Metrics**: Response times and resource usage
- **User Analytics**: Popular chart types and configurations

## Deployment Architecture

### Development
- **Local Development**: Direct Python execution with file-based config
- **Testing**: In-memory configuration with mock external dependencies

### Production
- **Docker Container**: Isolated environment with resource limits
- **Configuration**: Environment variables and mounted config files
- **Monitoring**: Log aggregation and metrics collection
- **Scaling**: Load balancer with multiple container instances

## Future Enhancements

### Short-term (Next Release)
1. **Comprehensive Test Suite**: Unit and integration tests
2. **Performance Monitoring**: Request timing and resource usage
3. **Enhanced Error Messages**: More detailed user-facing errors

### Medium-term
1. **Caching Layer**: Chart result caching for performance
2. **Async Support**: Non-blocking chart generation
3. **Plugin System**: Third-party chart type extensions

### Long-term
1. **Interactive Charts**: Advanced interactive visualization support
2. **Real-time Updates**: WebSocket support for live data
3. **Advanced Analytics**: Built-in statistical analysis tools

---

## Additional Resources

- **[API Documentation](api.md)**: Complete tool specifications
- **[Integration Guide](integration.md)**: MCP client setup
- **[Configuration Reference](configuration.md)**: All configuration options
- **[Contributing Guide](../CONTRIBUTING.md)**: Development workflow and standards

This architecture document is maintained alongside the codebase and updated with each significant architectural change.
