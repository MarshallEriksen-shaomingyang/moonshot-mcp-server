# Docker Setup for Moonshot MCP Server

This document explains how to run the Moonshot MCP Server using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

### 1. Configuration

Before running the Docker container, make sure you have the following configuration files:

- `.env` - Environment variables (copy from `.env.example` if needed)
- `moonshot_config.toml` - MCP server configuration (copy from `moonshot_config.example.toml` if needed)

### 2. Building and Running with Docker Compose

```bash
# Build and start the container in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 3. Building and Running with Docker

If you prefer to use Docker directly:

```bash
# Build the Docker image
docker build -t moonshot-mcp-server .

# Run the container
docker run -p 8000:8000 \
  -v $(pwd)/moonshot_config.toml:/app/moonshot_config.toml \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/logs:/app/logs \
  --name moonshot-mcp-server \
  moonshot-mcp-server
```

## Configuration

### Port Configuration

The default port is 8000. If you want to change it:

1. Update the `port` in `moonshot_config.toml`
2. Update the port mapping in `docker-compose.yml`

Example in `docker-compose.yml`:
```yaml
ports:
  - "8090:8090"  # Changed from 8000:8000
```

### Volume Mounts

The Docker setup includes the following volume mounts:

- `./moonshot_config.toml:/app/moonshot_config.toml` - Configuration file
- `./src:/app/src` - Source code (for development)
- `./.env:/app/.env` - Environment variables
- `./logs:/app/logs` - Logs directory

## Troubleshooting

### Port Conflicts

If you encounter port conflicts, you can change the external port in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Maps container port 8000 to host port 8001
```

### Permission Issues

If you encounter permission issues with the logs directory:

```bash
# Create the logs directory with proper permissions
mkdir -p logs
chmod 777 logs
```

### Container Not Starting

Check the logs for errors:

```bash
docker-compose logs
```
