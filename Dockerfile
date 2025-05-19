FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir --user uv && \
    uv --version

# Copy requirements first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Copy project files
COPY . .

# Create necessary configuration files if they don't exist
RUN if [ ! -f .env ]; then cp .env.example .env; fi && \
    if [ ! -f moonshot_config.toml ]; then cp moonshot_config.example.toml moonshot_config.toml; fi

# Expose the port (default is 8090 as per config)
EXPOSE 8090

# Command to run the application
CMD ["uv", "run", "server.py"]