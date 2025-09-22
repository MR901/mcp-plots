FROM python:3.10-slim

ARG APP_DIR=/app
WORKDIR ${APP_DIR}

# System deps for matplotlib (fonts, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libfreetype6 \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ${APP_DIR}/pyproject.toml
COPY src/ ${APP_DIR}/src/
COPY README.md ${APP_DIR}/README.md

# Install Python deps
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir .

# Runtime env
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=${APP_DIR} \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    LOG_LEVEL=INFO

EXPOSE 8000

# Run the MCP server (HTTP mode by default)
CMD ["python", "-m", "src", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
