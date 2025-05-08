# Multi-stage build for fogis_api_client

# Stage 1: Build dependencies
FROM python:3.11-slim-bullseye AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only the files needed for installation
COPY setup.py .
COPY README.md .
COPY fogis_api_client/ ./fogis_api_client/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip install --no-cache-dir marshmallow>=3.26.0 && \
    pip install --no-cache-dir jsonschema>=4.17.3 && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime image
FROM python:3.11-slim-bullseye

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Stockholm

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY fogis_api_client/ ./fogis_api_client/
COPY fogis_api_gateway.py .
COPY fogis_api_client_http_wrapper.py .
COPY fogis_api_client_swagger.py .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chmod -R 755 /app/logs /app/data

# Add health check
# Use a more robust health check that doesn't rely on specific response format
# Use 0.0.0.0 instead of localhost to ensure it works in all network configurations
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -s -o /dev/null -w '%{http_code}' http://0.0.0.0:8080/health | grep -q 200 || exit 1

# Add metadata labels
LABEL org.opencontainers.image.title="FOGIS API Client" \
      org.opencontainers.image.description="API Client for the Swedish Football Association's FOGIS system" \
      org.opencontainers.image.source="https://github.com/timmybird/fogis_api_client_python" \
      org.opencontainers.image.vendor="FOGIS API Client Contributors" \
      org.opencontainers.image.licenses="MIT"

# Command to run when the container starts
CMD ["python", "fogis_api_gateway.py"]
