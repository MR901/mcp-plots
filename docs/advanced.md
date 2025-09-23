# Advanced Guide

Architecture, deployment, and extension topics for power users and developers.

## Architecture Overview

### Component Structure
```
mcp-plots/
├── src/
│   ├── app/server.py           # MCP server implementation
│   ├── capabilities/
│   │   ├── tools.py           # MCP tool definitions
│   │   └── prompts.py         # AI prompt templates
│   └── visualization/
│       ├── generator.py       # Matplotlib chart generation
│       ├── mermaid_generator.py # Mermaid syntax generation
│       └── chart_config.py    # Configuration schemas
```

### Data Flow
1. **MCP Client** → JSON-RPC request
2. **Server** → Parse and validate parameters  
3. **Tools** → Route to appropriate generator
4. **Generator** → Create chart (Mermaid/Image)
5. **Server** → Return MCP-formatted response

### Design Principles
- **Mermaid-first**: Universal compatibility via text-based charts
- **Zero-configuration**: Intelligent defaults, minimal setup
- **Extensible**: Plugin architecture for custom chart types
- **Stateless**: No persistent storage, memory-only processing

## Deployment Options

### Production PyPI Installation
```bash
pip install mcp-plots
mcp-plots --transport streamable-http --host 0.0.0.0 --port 8000
```

**Use cases**: Shared team servers, containerized deployments

### Development Installation  
```bash
git clone https://github.com/mr901/mcp-plots.git
cd mcp-plots
pip install -e .
python -m src --transport stdio --debug
```

**Use cases**: Local development, custom modifications

### Container Deployment
```dockerfile
FROM python:3.11-slim
RUN pip install mcp-plots
EXPOSE 8000
CMD ["mcp-plots", "--transport", "streamable-http", "--host", "0.0.0.0"]
```

**Use cases**: Cloud deployment, service orchestration

### uvx Deployment (Legacy)
```bash
uvx --from git+https://github.com/mr901/mcp-plots.git mcp-plots
```

**Use cases**: Direct git installation, bleeding-edge features

## Configuration Management

### Environment-based Configuration
```bash
export MCP_TRANSPORT=streamable-http
export MCP_HOST=0.0.0.0  
export MCP_PORT=8000
export LOG_LEVEL=INFO
export CHART_DEFAULT_WIDTH=1000
export CHART_DEFAULT_HEIGHT=700
mcp-plots
```

### Configuration File (Advanced)
```python
# ~/.mcp-plots-config.py
CHART_CONFIG = {
    'default_theme': 'dark',
    'default_width': 1200,
    'default_height': 800,
    'max_data_points': 50000,
    'custom_themes': {
        'corporate': ['#1f77b4', '#ff7f0e', '#2ca02c']
    }
}
```

### Runtime Configuration API
```javascript
// Configure via MCP tools
configure_preferences({
  theme: "dark",
  chart_width: 1000,
  chart_height: 700
})
```

## Performance Optimization

### Memory Management
```python
# Increase data point limit
export CHART_MAX_DATA_POINTS=100000

# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB")
```

### Chart Generation Optimization
```python
# Pre-load matplotlib backends
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Optimize for batch processing  
config_overrides = {
    'dpi': 72,  # Lower DPI for faster generation
    'show_grid': False,  # Disable grid for performance
}
```

### Concurrent Processing
```python
# Custom server with thread pool
from concurrent.futures import ThreadPoolExecutor
import asyncio

class OptimizedMCPServer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def render_chart(self, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._render_sync, 
            kwargs
        )
```

## Custom Chart Types

### Extending the Generator
```python
# src/visualization/custom_generator.py
from .generator import ChartGenerator
from .chart_config import ChartType

class CustomChartGenerator(ChartGenerator):
    @staticmethod
    def generate_violin_chart(chart_data, config):
        """Custom violin plot implementation."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        # Your custom chart logic here
        data = CustomChartGenerator._prepare_data(chart_data)
        ax.violinplot(data[config.value_field])
        
        return CustomChartGenerator._save_chart(fig, config)
```

### Registering New Chart Types
```python
# Add to ChartType enum
class ChartType(Enum):
    # ... existing types
    VIOLIN = "violin"

# Register in generator
def generate_chart(chart_type, data, config):
    if chart_type == ChartType.VIOLIN:
        return CustomChartGenerator.generate_violin_chart(data, config)
```

### Custom Mermaid Generators
```python
# src/visualization/custom_mermaid.py
class CustomMermaidGenerator:
    @staticmethod
    def generate_violin_mermaid(chart_data, config):
        """Generate Mermaid representation of violin plot."""
        # Mermaid doesn't support violin plots directly
        # Convert to boxplot representation
        return MermaidGenerator.generate_boxplot_mermaid(chart_data, config)
```

## Security Considerations

### Network Security
```python
# Restrict network access
import socket

def create_secure_server():
    # Bind only to localhost
    server = MCPServer(host='127.0.0.1', port=8000)
    
    # Implement request filtering
    def validate_request(request):
        # Add custom validation logic
        return True
    
    server.add_middleware(validate_request)
```

### Data Sanitization  
```python
# Input validation
def sanitize_chart_data(data):
    """Sanitize input data for security."""
    if len(data) > MAX_DATA_POINTS:
        raise ValueError(f"Too many data points: {len(data)}")
    
    for item in data:
        for key, value in item.items():
            if isinstance(value, str) and len(value) > 1000:
                raise ValueError(f"String too long in field {key}")
    
    return data
```

### Resource Limits
```python  
# Memory and CPU limits
import resource

def set_resource_limits():
    # Limit memory to 1GB
    resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, -1))
    
    # Limit CPU time per request
    resource.setrlimit(resource.RLIMIT_CPU, (30, -1))
```

## Monitoring and Observability

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

def log_chart_generation(chart_type, data_points, duration):
    logger.info(
        "chart_generated",
        chart_type=chart_type,
        data_points=data_points,
        duration_ms=duration * 1000,
        memory_mb=get_memory_usage()
    )
```

### Metrics Collection
```python
from prometheus_client import Counter, Histogram, start_http_server

CHART_REQUESTS = Counter('mcp_plots_requests_total', 'Total chart requests', ['chart_type'])
GENERATION_TIME = Histogram('mcp_plots_generation_seconds', 'Chart generation time')

@GENERATION_TIME.time()
def render_chart_with_metrics(chart_type, **kwargs):
    CHART_REQUESTS.labels(chart_type=chart_type).inc()
    return render_chart(chart_type, **kwargs)

# Start metrics endpoint
start_http_server(9090)
```

### Health Checks
```python
def health_check():
    """System health check endpoint."""
    try:
        # Test chart generation
        test_data = [{"x": 1, "y": 2}]
        render_chart("scatter", data=test_data, 
                    field_map={"x_field": "x", "y_field": "y"})
        
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Testing and Quality Assurance

### Unit Testing
```python
import pytest
from src.visualization.generator import ChartGenerator

def test_bar_chart_generation():
    data = [{"category": "A", "value": 10}]
    config = ChartConfig(output_format=OutputFormat.MERMAID)
    result = ChartGenerator.generate_bar_chart(data, config)
    assert "bar" in result.lower()
    assert "A" in result
```

### Integration Testing
```python
def test_mcp_server_integration():
    """Test full MCP server integration."""
    server = create_test_server()
    response = server.call_tool("render_chart", {
        "chart_type": "bar",
        "data": [{"cat": "A", "val": 10}],
        "field_map": {"category_field": "cat", "value_field": "val"}
    })
    assert response["status"] == "success"
```

### Load Testing
```bash
# Artillery.js load test config
artillery quick \
  --count 100 \
  --num 10 \
  http://localhost:8000/health
```

## Publishing and Distribution

### PyPI Publishing Workflow
```bash
# Build package
python -m build

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ mcp-plots

# Upload to production PyPI
twine upload dist/*
```

### MCP Registry Publishing (mcp-publisher)
Use the MCP Registry publisher to register or update this server in the MCP Registry using the `server.json` in the repo root.

Prerequisites:
- Ensure `server.json` is valid and the version matches `pyproject.toml`.

Publish to MCP Registry:
```bash
# mcp-publisher init
mcp-publisher login github
mcp-publisher publish
```

Optional: Minimal GitHub Actions workflow
```yaml
name: MCP Publish
on:
  push:
    tags: ['v*.*.*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          python -m pip install --upgrade pip
          pip install mcp-publisher
      - run: mcp-publisher publish
        env:
          MCP_API_KEY: ${{ secrets.MCP_API_KEY }}
```

References:
- MCP Registry publishing guide: https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/github-actions.md
- Publish a server guide: https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md
- Example repository workflows: https://github.com/upstash/context7/tree/master/.github

### Version Management
```python
# Semantic versioning in pyproject.toml
version = "1.2.3"  # MAJOR.MINOR.PATCH

# Automated version bumping
pip install bump2version
bump2version patch  # 1.2.3 -> 1.2.4
```

### Release Automation
```yaml
# GitHub Actions workflow
name: Release
on:
  push:
    tags: ['v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and publish
        run: |
          python -m build
          twine upload dist/*
```

## Development Setup

### Local Development Environment
```bash
git clone https://github.com/mr901/mcp-plots.git
cd mcp-plots
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Code Quality Tools
```bash
# Formatting
black src/ tests/
isort src/ tests/

# Type checking  
mypy src/

# Linting
flake8 src/ tests/

# Testing
pytest tests/ --cov=src
```

### Development Server
```bash
# Run with auto-reload
python -m src --transport stdio --debug --log-level DEBUG

# Test specific features
python -c "
from src.capabilities.tools import render_chart
result = render_chart('help')
print(result)
"
```
