# ZAP MCP Server - Podman Setup

This document describes how to run the ZAP MCP Server using Podman and Podman Compose, with specific considerations for Podman's unique features.

## ⚠️ IMPORTANT: Automatic Localhost URL Transformation

**✅ AUTOMATIC TRANSFORMATION:** The server now automatically detects Podman environments and transforms `localhost`/`127.0.0.1` URLs to `host.containers.internal`:

```bash
# ✅ These URLs are automatically transformed in Podman:
URL: http://localhost:3000     → http://host.containers.internal:3000
URL: http://127.0.0.1:8080    → http://host.containers.internal:8080
URL: https://localhost:8443    → https://host.containers.internal:8443

# ✅ You can now use localhost URLs directly!
```

**This means you no longer need to manually replace `localhost` with `host.containers.internal` - it happens automatically!**

## Prerequisites

- Podman and Podman Compose installed
- At least 4GB RAM for the container
- Ports 8080 and 8082 available
- Firefox ESR installed in container (for AJAX scans)

### Installing Podman Compose

```bash
# Install podman-compose
pip install podman-compose

# Or using your system package manager
# Ubuntu/Debian:
sudo apt install podman-compose

# Fedora/RHEL:
sudo dnf install podman-compose
```

## Quick Start

### Option 1: Host Gateway (Recommended)

```bash
# Build container
./build.sh

# Start container (auto-detects Podman)
./start.sh

# Check status
podman-compose ps
```

**⚠️ CRITICAL: For localhost scans, you can now use:**
- `http://localhost:3000` (automatically transformed to `http://host.containers.internal:3000`)
- `http://127.0.0.1:8080` (automatically transformed to `http://host.containers.internal:8080`)
- **No manual URL replacement needed!**

## Podman-Specific Configuration

### Using podman-compose.yml

The project includes a dedicated `podman-compose.yml` file optimized for Podman:

```yaml
version: '3.8'

services:
  zap-mcp:
    build: .
    container_name: zap-custom-mcp
    ports:
      - "8080:8080"  # ZAP API
      - "8082:8082"  # MCP HTTP
    environment:
      # ZAP Configuration
      ZAP_BASE: http://127.0.0.1:8080
      ZAP_AUTOSTART: "true"
      ZAP_SESSION_NAME: zap_podman_session
      ZAP_SESSION_STRATEGY: unique
      ZAP_LOG_LEVEL: INFO
      ZAP_STARTUP_TIMEOUT: "120"
      ZAP_LONG_SCAN_TIMEOUT: "14400"

      # MCP Configuration
      ZAP_MCP_HOST: 0.0.0.0
      ZAP_MCP_PORT: "8082"
      ZAP_MCP_PATH: /mcp

    # Host accessible from container (Linux + Windows)
    extra_hosts:
      - "host.containers.internal:host-gateway"

    volumes:
      - zap-data:/opt/zap/session
      - ./logs:/app/logs

    restart: unless-stopped
```

### Podman vs Docker Differences

| Feature | Docker | Podman |
|---------|--------|--------|
| Host Gateway | `host.docker.internal` | `host.containers.internal` |
| Rootless | Optional | Default |
| Daemon | Required | Not required |
| Security | Less secure by default | More secure by default |
| Compose | `docker-compose` | `podman-compose` |

## Localhost Scanning with Podman

### ⚠️ CRITICAL PROBLEM
Podman containers are isolated by default. **`localhost` in the container points to the container itself, not the host!**

**This means:**
- ❌ `http://localhost:3000` will NOT reach your local development server
- ❌ `http://localhost:8080` will NOT reach your local API
- ❌ Any `localhost` URL will fail when scanning from Podman containers

**You MUST use `host.containers.internal` instead of `localhost` for all localhost applications!**

### ✅ AUTOMATIC SOLUTION

**The server automatically handles localhost URL transformation:**

```bash
# ✅ These work automatically in Podman:
http://localhost:3000     → http://host.containers.internal:3000
http://127.0.0.1:8080    → http://host.containers.internal:8080
https://localhost:8443    → https://host.containers.internal:8443

# ✅ You can use localhost URLs directly!
```

**No manual URL replacement needed - the server detects Podman and transforms URLs automatically!**

## Podman-Specific Commands

### Basic Operations

```bash
# Start containers
podman-compose up -d

# Follow logs
podman-compose logs -f

# Stop containers
podman-compose down

# Rebuild containers
podman-compose build

# Check status
podman-compose ps
```

### Rootless Podman Considerations

**Podman runs rootless by default, which is more secure:**

```bash
# Check if running rootless
podman info | grep "rootless"

# If you need root privileges (not recommended)
sudo podman-compose up -d
```

### Podman Socket Access

```bash
# Enable Podman socket for Docker-compatible tools
systemctl --user enable podman.socket

# Check socket status
systemctl --user status podman.socket
```

## Configuration

**📖 For complete configuration details, see [README.md](README.md#-configuration)**

### Podman-Specific Settings

- `ZAP_SESSION_NAME`: Session Name (Default: `zap_podman_session`)
- `ZAP_MCP_HOST`: MCP Server Host (Default: `0.0.0.0`)

### Volumes

- `zap-data`: Persistent ZAP sessions
- `./logs`: Log files

## Access

**📖 For complete access information, see [README.md](README.md#-quick-start)**

After startup, the following services are available:

- **ZAP API**: http://localhost:8080
- **MCP Server**: http://localhost:8082/mcp

## AJAX Scans

The container includes Firefox ESR for AJAX spider scans:

- **Browser**: Firefox ESR (headless mode)
- **No X11 Required**: Runs completely headless without display server
- **Environment**: `MOZ_HEADLESS=1` with all sandbox features disabled
- **JVM Options**: Headless mode with OpenGL disabled
- **Default Configuration**: Uses `firefox-headless` browser ID

AJAX scans will automatically use the Firefox browser in headless mode without requiring any display server.

## Example Scans

### Automatic URL Transformation
```bash
# Test ZAP API directly
curl http://localhost:8080/JSON/core/view/version/

# Test MCP Server
curl http://localhost:8082/mcp

# ✅ AUTOMATIC: Scan localhost app (URLs are automatically transformed)
# ✅ CORRECT: http://localhost:3000 (automatically becomes http://host.containers.internal:3000)
# ✅ CORRECT: http://127.0.0.1:8080 (automatically becomes http://host.containers.internal:8080)
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
podman-compose logs zap-mcp

# Check container status
podman-compose ps

# Check Podman service
podman system info
```

### ZAP Won't Start

```bash
# Log into container
podman-compose exec zap-mcp bash

# Check ZAP status
curl http://localhost:8080/JSON/core/view/version/
```

### Localhost Access Doesn't Work

**✅ AUTOMATIC TRANSFORMATION:** The server automatically transforms `localhost` URLs to `host.containers.internal`. If you're still having issues:

```bash
# ✅ CORRECT: Check if host.containers.internal is reachable
podman-compose exec zap-mcp curl http://host.containers.internal:3000

# ✅ ALSO CORRECT: Use localhost (automatically transformed)
podman-compose exec zap-mcp curl http://localhost:3000

# If host.containers.internal doesn't work, try host IP address
podman-compose exec zap-mcp curl http://172.17.0.1:3000
```

**The server automatically handles URL transformation - you can use `localhost` URLs directly!**

### Podman-Specific Issues

#### Rootless Permission Issues

```bash
# Check if running rootless
podman info | grep "rootless"

# If permission issues, check user namespaces
podman unshare --rootless-netns ip addr
```

#### Socket Connection Issues

```bash
# Check Podman socket
podman system info

# Restart Podman service
systemctl --user restart podman.socket
```

#### Port Conflicts

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

## Security Advantages of Podman

- **Rootless by default**: More secure than Docker
- **No daemon required**: Reduced attack surface
- **User namespaces**: Better isolation
- **No privileged containers**: Enhanced security

## Updates

```bash
# Rebuild image
./build.sh

# Restart container
podman-compose down
podman-compose up -d
```

## Solution Comparison

| Solution | Advantages | Disadvantages | Recommendation |
|----------|------------|---------------|----------------|
| Host Gateway | Secure, isolated, flexible | None (automatic URL transformation) | ✅ **Recommended** |

## Usage with MCP Clients

**📖 For complete MCP client usage instructions, see [README.md](README.md#-connect-your-mcp-client)**

The Podman container provides the MCP server via HTTP at: `http://localhost:8082/mcp`

## Advanced Configuration

**📖 For advanced configuration options, see [README.md](README.md#-configuration)**

### Podman-Specific Advanced Options

- Custom ZAP versions
- Additional ZAP addons
- Persistent session management
- Rootless Podman considerations

## Migration from Docker

If you're migrating from Docker to Podman:

1. **Install Podman Compose**: `pip install podman-compose`
2. **Update commands**: `docker-compose` → `podman-compose`
3. **Check permissions**: Ensure rootless Podman has necessary permissions
4. **URL transformation is automatic**: No manual changes needed for `localhost` URLs

## Best Practices

1. **Use rootless Podman** for better security
2. **Use `localhost` URLs directly** - automatic transformation handles the rest
3. **Monitor resource usage** with `podman stats`
4. **Clean up regularly** with `podman system prune`
5. **Use Podman Compose** for multi-container applications

## Support

- 📖 [Podman Documentation](https://docs.podman.io/)
- 🐛 [Podman Issues](https://github.com/containers/podman/issues)
- 💬 [Podman Community](https://podman.io/community/)

---

**Podman: The secure, daemonless container engine for Linux!**
