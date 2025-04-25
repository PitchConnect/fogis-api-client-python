FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fogis-api-client-timmybird python-dotenv

# Copy the session keeper tools
COPY tools/session_keeper /app/session_keeper

# Create data directory for persistence
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app

# Volume for persistent data
VOLUME /app/data

# Set working directory to data for file outputs
WORKDIR /app/data

# Default command shows help
ENTRYPOINT ["python", "/app/session_keeper/fogis_tools.py"]
