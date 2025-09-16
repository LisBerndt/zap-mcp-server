#!/bin/bash
set -e

echo "Starting ZAP MCP Server..."

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    COMPOSE_CMD="podman-compose"
    echo "Using Podman as container runtime"
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    COMPOSE_CMD="docker-compose"
    echo "Using Docker as container runtime"
else
    echo "Error: Neither Docker nor Podman found!"
    exit 1
fi

# Start with compose
$COMPOSE_CMD up -d

echo "ZAP MCP Server is starting..."
echo "ZAP API will be available at: http://localhost:8080"
echo "MCP Server will be available at: http://localhost:8082/mcp"
echo ""
echo "✅ AUTOMATIC URL TRANSFORMATION ENABLED:"
echo "   - localhost URLs are automatically mapped to host.docker.internal (Docker)"
echo "   - localhost URLs are automatically mapped to host.containers.internal (Podman)"
echo "   - You can use localhost URLs directly - no manual mapping needed!"
echo ""
echo "Examples:"
echo "   http://localhost:3000  →  http://host.docker.internal:3000 (Docker)"
echo "   http://localhost:3000  →  http://host.containers.internal:3000 (Podman)"
echo ""
echo "To view logs: $COMPOSE_CMD logs -f"
echo "To stop: $COMPOSE_CMD down"

