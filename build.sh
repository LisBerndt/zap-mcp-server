#!/bin/bash
set -e

echo "Building ZAP MCP Docker/Podman image..."

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    echo "Using Podman as container runtime"
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    echo "Using Docker as container runtime"
else
    echo "Error: Neither Docker nor Podman found!"
    exit 1
fi

# Build the container image
$CONTAINER_RUNTIME build -t zap-custom-mcp:latest .

echo "Build completed successfully!"
echo ""
echo "To run the container:"
if [ "$CONTAINER_RUNTIME" = "podman" ]; then
    echo "  podman-compose up -d"
    echo "Or manually:"
    echo "  podman run -p 8080:8080 -p 8082:8082 zap-custom-mcp:latest"
else
    echo "  docker-compose up -d"
    echo "Or manually:"
    echo "  docker run -p 8080:8080 -p 8082:8082 zap-custom-mcp:latest"
fi

