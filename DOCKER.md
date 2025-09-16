# ZAP MCP Server - Docker Setup

This document describes how to run the ZAP MCP Server in a Docker container and how to scan localhost applications.

## ⚠️ IMPORTANT: Automatic Localhost URL Transformation

**✅ AUTOMATIC TRANSFORMATION:** The server now automatically detects Docker environments and transforms `localhost`/`127.0.0.1` URLs to `host.docker.internal`:

```bash
# ✅ These URLs are automatically transformed in Docker:
URL: http://localhost:3000     → http://host.docker.internal:3000
URL: http://127.0.0.1:8080    → http://host.docker.internal:8080
URL: https://localhost:8443    → https://host.docker.internal:8443

# ✅ You can now use localhost URLs directly!
```

**This means you no longer need to manually replace `localhost` with `host.docker.internal` - it happens automatically!**

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM for the container
- Ports 8080 and 8082 available

## Quick Start

### Option 1: Host Gateway (Recommended)

```bash
# Build container
./build.sh

# Start container
./start.sh

# Check status
docker-compose ps
```

**⚠️ CRITICAL: For localhost scans, you can now use:**
- `http://localhost:3000` (automatically transformed to `http://host.docker.internal:3000`)
- `http://127.0.0.1:8080` (automatically transformed to `http://host.docker.internal:8080`)
- **No manual URL replacement needed!**

## Localhost Scanning

### ⚠️ CRITICAL PROBLEM
Docker containers are isolated by default. **`localhost` in the container points to the container itself, not the host!**

**This means:**
- ❌ `http://localhost:3000` will NOT reach your local development server
- ❌ `http://localhost:8080` will NOT reach your local API
- ❌ Any `localhost` URL will fail when scanning from Docker containers

**You MUST use `host.docker.internal` instead of `localhost` for all localhost applications!**

### ✅ AUTOMATIC SOLUTION

**The server automatically handles localhost URL transformation:**

```bash
# ✅ These work automatically in Docker:
http://localhost:3000     → http://host.docker.internal:3000
http://127.0.0.1:8080    → http://host.docker.internal:8080
https://localhost:8443    → https://host.docker.internal:8443

# ✅ You can use localhost URLs directly!
```

**No manual URL replacement needed - the server detects Docker and transforms URLs automatically!**

## Configuration

**📖 For complete configuration details, see [README.md](README.md#-configuration)**

### Docker-Specific Settings

- `ZAP_SESSION_NAME`: Session Name (Default: `zap_docker_session`)
- `ZAP_MCP_HOST`: MCP Server Host (Default: `0.0.0.0`)

### Volumes

- `zap-data`: Persistent ZAP sessions
- `./logs`: Log files

## Access

**📖 For complete access information, see [README.md](README.md#-quick-start)**

After startup, the following services are available:

- **ZAP API**: http://localhost:8080
- **MCP Server**: http://localhost:8082/mcp

## Example Scans

### Automatic URL Transformation
```bash
# Test ZAP API directly
curl http://localhost:8080/JSON/core/view/version/

# Test MCP Server
curl http://localhost:8082/mcp

# ✅ AUTOMATIC: Scan localhost app (URLs are automatically transformed)
# ✅ CORRECT: http://localhost:3000 (automatically becomes http://host.docker.internal:3000)
# ✅ CORRECT: http://127.0.0.1:8080 (automatically becomes http://host.docker.internal:8080)
```

### Example with OWASP Juice Shop
```bash
# Scan OWASP Juice Shop (publicly available test target)
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "start_complete_scan",
    "arguments": {
      "url": "https://juice-shop.herokuapp.com/#/",
      "include_findings": true
    }
  }'
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs zap-mcp

# Check container status
docker-compose ps
```

### ZAP Won't Start

```bash
# Log into container
docker-compose exec zap-mcp bash

# Check ZAP status
curl http://localhost:8080/JSON/core/view/version/
```

### Localhost Access Doesn't Work

**✅ AUTOMATIC TRANSFORMATION:** The server automatically transforms `localhost` URLs to `host.docker.internal`. If you're still having issues:

```bash
# ✅ CORRECT: Check if host.docker.internal is reachable
docker-compose exec zap-mcp curl http://host.docker.internal:3000

# ✅ ALSO CORRECT: Use localhost (automatically transformed)
docker-compose exec zap-mcp curl http://localhost:3000

# If host.docker.internal doesn't work, try host IP address
docker-compose exec zap-mcp curl http://172.17.0.1:3000
```

**The server automatically handles URL transformation - you can use `localhost` URLs directly!**

### Port Conflicts

If ports are already in use, configure custom ports:

**Using .env file (Recommended):**

```bash
# Copy the example file
cp env.example .env

# Edit .env file
ZAP_PORT=8081
ZAP_MCP_PORT=8083
ZAP_BASE=http://127.0.0.1:8081
```

**Using environment variables:**

```bash
# Set custom ports
export ZAP_PORT=8081
export ZAP_MCP_PORT=8083
export ZAP_BASE="http://127.0.0.1:8081"

# Then start containers
./start.sh
```

**Connect to**: `http://localhost:8083/mcp`

## Performance Tuning

### Memory

For large scans, increase available memory:

```yaml
services:
  zap-mcp:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### CPU

```yaml
services:
  zap-mcp:
    deploy:
      resources:
        limits:
          cpus: '4.0'
        reservations:
          cpus: '2.0'
```

## Security

- Container runs as non-root user (`zap`)
- ZAP API keys are disabled by default
- Only necessary ports are exposed

## Updates

```bash
# Rebuild image
./build.sh

# Restart container
docker-compose down
docker-compose up -d
```

## Solution Comparison

| Solution | Advantages | Disadvantages | Recommendation |
|----------|------------|---------------|----------------|
| Host Gateway | Secure, isolated, flexible | None (automatic URL transformation) | ✅ **Recommended** |

## Usage with MCP Clients

**📖 For complete MCP client usage instructions, see [README.md](README.md#-connect-your-mcp-client)**

The Docker container provides the MCP server via HTTP at: `http://localhost:8082/mcp`

## Advanced Configuration

**📖 For advanced configuration options, see [README.md](README.md#-configuration)**

### Docker-Specific Advanced Options

- Custom ZAP versions
- Additional ZAP addons
- Persistent session management



