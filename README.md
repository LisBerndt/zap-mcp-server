# ZAP MCP Server

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OWASP ZAP](https://img.shields.io/badge/OWASP-ZAP-red.svg)](https://www.zaproxy.org/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Protocol-green.svg)](https://modelcontextprotocol.io/)

A powerful **Model Context Protocol (MCP) Server** that integrates **OWASP ZAP** (Zed Attack Proxy) with AI assistants and MCP clients. Enable AI-powered security testing through automated vulnerability scanning.

## 🎯 Why ZAP MCP Server?

**Shift Left Security** - Empower developers to integrate security testing early in the development lifecycle. Instead of waiting for security reviews at the end of development, developers can now:

- **🔧 Test during development** - Run security scans on localhost applications
- **🤖 AI-assisted security** - Get intelligent vulnerability analysis through AI assistants
- **⚡ Rapid feedback** - Identify security issues before they reach production
- **🔄 CI/CD integration** - Automate security testing in development workflows
- **📊 Developer-friendly** - Simple MCP interface for non-security experts

## 🚀 Features

- **🔍 Multiple Scan Types**: Active, Passive, AJAX Spider, and Complete scans
- **⚡ Asynchronous Processing**: Background scan execution with real-time status updates
- **🐳 Docker Support**: Easy deployment with Docker Compose
- **🤖 AI Integration**: Seamless integration with MCP-compatible AI assistants
- **📊 Rich Reporting**: Detailed vulnerability reports with risk scoring
- **🔄 Session Management**: Flexible session handling strategies
- **🛡️ Production Ready**: Robust error handling and logging

## 📋 Prerequisites

- **Python 3.8+**
- **OWASP ZAP** installed and accessible via PATH
- **Java** (required by ZAP)
- **Docker** or **Podman** (optional, for containerized deployment)

**📖 For container-specific prerequisites, see:**
- **[DOCKER.md](DOCKER.md)** - Docker prerequisites and setup
- **[PODMAN.md](PODMAN.md)** - Podman prerequisites and setup

## 🛠️ Installation

### Package Structure

This project uses a proper Python package structure (`zap_custom_mcp/`) which provides several benefits:

- **✅ Clean imports** - Proper module organization
- **✅ Docker compatibility** - Works seamlessly in containers  
- **✅ PyPI ready** - Can be published as a proper Python package

**Execution methods:**
- `python -m zap_custom_mcp` (recommended)
- `python -m zap_custom_mcp.http_server` (alternative method)

### Option 1: Local Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/LisBerndt/zap-custom-mcp.git
   cd zap-custom-mcp
   ```

2. **Install OWASP ZAP**

   - Download from [OWASP ZAP Downloads](https://www.zaproxy.org/download/)
   - Ensure `zap.bat` is accessible via PATH
   - Test: `where zap.bat` (Windows) or `which zap.sh` (Linux/Mac)

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Docker/Podman Deployment (Recommended)

**🐳 Docker/Podman is the easiest and most reliable method!**

```bash
# 1. Clone repository
git clone https://github.com/LisBerndt/zap-custom-mcp.git
cd zap-custom-mcp

# 2. Build and start containers (auto-detects Docker/Podman)
# Linux/Mac:
./build.sh
./start.sh

# Windows:
build.bat
start.bat

# 3. Check status
docker-compose ps  # or podman-compose ps
```

**📖 For detailed Docker/Podman setup and localhost scanning instructions, see:**
- **[DOCKER.md](DOCKER.md)** - Complete Docker setup guide
- **[PODMAN.md](PODMAN.md)** - Complete Podman setup guide

**⚠️ CRITICAL:** When using containers, localhost applications must be accessed via `host.docker.internal` (Docker) or `host.containers.internal` (Podman) instead of `localhost`. This is the **only supported method** for localhost scanning.

## ⚙️ Configuration

The server uses environment variables for configuration. Key settings:

| Variable       | Default                 | Description                                           |
| -------------- | ----------------------- | ----------------------------------------------------- |
| `ZAP_BASE`     | `http://127.0.0.1:8080` | **ZAP API port** - Change port by modifying URL       |
| `ZAP_MCP_PORT` | `8082`                  | **MCP server port** - Port for MCP client connections |
| `ZAP_MCP_HOST` | `127.0.0.1`             | MCP server host (use `0.0.0.0` for all interfaces)    |
| `ZAP_AUTOSTART` | `true`                  | Auto-start ZAP if not running                         |
| `ZAP_LOG_LEVEL` | `INFO`                  | Logging level                                         |

### Custom Port Configuration

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

**📖 For complete configuration details, see:**
- **[DOCKER.md](DOCKER.md)** - Docker configuration options
- **[PODMAN.md](PODMAN.md)** - Podman configuration options

## 🚀 Quick Start

### 🐳 Docker/Podman (Recommended)

**Fastest start with containers:**

```bash
# 1. Clone repository
git clone https://github.com/LisBerndt/zap-custom-mcp.git
cd zap-custom-mcp

# 2. Start (auto-detects Docker/Podman)
# Linux/Mac:
./build.sh && ./start.sh

# Windows:
build.bat
start.bat

# 3. Wait (approx. 90 seconds) and then connect:
# http://localhost:8082/mcp
```

**📖 For detailed setup instructions and localhost scanning, see:**
- **[DOCKER.md](DOCKER.md)** - Complete Docker guide
- **[PODMAN.md](PODMAN.md)** - Complete Podman guide

**⚠️ CRITICAL:** For localhost scanning, use `host.docker.internal` (Docker) or `host.containers.internal` (Podman) instead of `localhost`. This is the **only supported method**.

### 💻 Local Installation

### 1. Start the Server

**Recommended method (as package):**
```bash
python -m zap_custom_mcp
```

**Alternative methods:**
```bash
# As specific module
python -m zap_custom_mcp.http_server

# Direct execution (legacy, may have import issues)
python zap_custom_mcp/http_server.py
```

**💡 Best Practice:** Always use `python -m zap_custom_mcp` for the most reliable execution.

The server will automatically:

- ✅ Check if ZAP is running
- ✅ Start ZAP if needed (via PATH)
- ✅ Create/load a session
- ✅ Start the MCP server

**⏱️ Important**: The server takes approximately **90 seconds** to become fully operational after startup. This includes:

- ZAP initialization and startup
- Session creation
- MCP server initialization
- All components becoming ready

### 2. Connect Your MCP Client

Connect to: `http://localhost:8082/mcp`

#### MCP Configuration Example

For Cursor IDE, add to your `mcp.json`:

```json
{
  "mcpServers": {
    "zap-mcp": {
      "url": "http://localhost:8082/mcp"
    }
  }
}
```

For other MCP clients, use the same URL endpoint.

### 3. Available Tools

| Tool                  | Description                                          |
| --------------------- | ---------------------------------------------------- |
| `start_active_scan`   | Run active security scan (Spider + Active)           |
| `start_complete_scan` | Run complete scan (AJAX + Spider + Active + Passive) |
| `start_passive_scan`  | Run passive security analysis                        |
| `start_ajax_scan`     | Run AJAX spider for modern web apps                  |
| `get_scan_status`     | Get real-time scan status                            |
| `cancel_scan`         | Cancel running scan                                  |
| `list_scans`          | List all active scans                                |
| `create_new_session`  | Create new ZAP session                               |

## 📖 Usage Examples

### Development Workflow Integration

**Local Development Testing:**

```json
{
  "tool": "start_passive_scan",
  "arguments": {
    "url": "http://localhost:3000",
    "timeout_seconds": 60
  }
}
```

**Pre-Commit Security Check:**

```json
{
  "tool": "start_active_scan",
  "arguments": {
    "url": "http://localhost:8080",
    "ascan_max_wait_seconds": 300,
    "spider_max_wait_seconds": 120
  }
}
```

**📖 For Docker/Podman localhost scanning examples, see:**
- **[DOCKER.md](DOCKER.md)** - Docker localhost examples
- **[PODMAN.md](PODMAN.md)** - Podman localhost examples

### Basic Security Scan

```json
{
  "tool": "start_complete_scan",
  "arguments": {
    "url": "https://example.com",
    "include_findings": true,
    "include_evidence": false
  }
}
```

### Quick Passive Scan

```json
{
  "tool": "start_passive_scan",
  "arguments": {
    "url": "https://example.com",
    "timeout_seconds": 300
  }
}
```

### Custom Active Scan

```json
{
  "tool": "start_active_scan",
  "arguments": {
    "url": "https://example.com",
    "ascan_max_wait_seconds": 3600,
    "spider_max_wait_seconds": 900,
    "scanPolicyName": "Default Policy"
  }
}
```

## 🔄 Shift Left Security Integration

### Development Workflows

**1. Local Development**

- Test your localhost application during development
- Get immediate feedback on security issues
- Fix vulnerabilities before committing code

**2. Pre-Commit Hooks**

- Integrate security scans into git pre-commit hooks
- Prevent insecure code from entering the repository
- Automated security validation

**3. CI/CD Pipeline Integration**

- Add security testing to your build pipeline
- Scan staging environments automatically
- Generate security reports for each deployment

**4. AI-Assisted Security**

- Use AI assistants to interpret scan results
- Get recommendations for fixing vulnerabilities
- Learn security best practices through AI guidance

### Benefits for Development Teams

- **⚡ Faster feedback** - Catch issues in minutes, not weeks
- **💰 Cost reduction** - Fix issues early when they're cheaper to resolve
- **🎯 Developer education** - Learn security through hands-on testing
- **🛡️ Proactive security** - Build secure applications from the start
- **📊 Continuous improvement** - Regular security assessments

## 🐳 Container Deployment

**📖 For complete container setup and usage instructions, see:**
- **[DOCKER.md](DOCKER.md)** - Complete Docker setup guide with localhost scanning
- **[PODMAN.md](PODMAN.md)** - Complete Podman setup guide with localhost scanning

**Quick container commands:**
```bash
# Start containers (auto-detects Docker/Podman)
# Linux/Mac:
./start.sh

# Windows:
start.bat

# Follow logs
docker-compose logs -f    # Docker
podman-compose logs -f    # Podman

# Stop containers
docker-compose down       # Docker
podman-compose down       # Podman
```

## 📊 Scan Results

Scans return structured results including:

```json
{
  "scan_id": "abc12345",
  "target": "https://example.com",
  "alerts": {
    "High": 2,
    "Medium": 5,
    "Low": 12,
    "Informational": 8
  },
  "totalAlerts": 27,
  "riskScore": 31,
  "vulnerabilityNames": [
    { "name": "SQL Injection", "risk": "High", "count": 1 },
    { "name": "XSS", "risk": "Medium", "count": 3 }
  ],
  "durations": {
    "ajax": 45.2,
    "spider": 120.5,
    "ascan": 1800.0,
    "pscan": 30.1
  }
}
```

## 🔧 Troubleshooting

### Server Takes Too Long to Start

The server requires approximately **90 seconds** to become fully operational. This is normal and includes:

- ZAP startup and initialization
- Session creation
- MCP server initialization

**Wait for the startup process to complete** before attempting to connect.

### ZAP Won't Start

```bash
# Check if ZAP is in PATH
where zap.bat  # Windows
which zap.sh   # Linux/Mac

# Check Java installation
java -version

# Enable debug logging
set ZAP_LOG_LEVEL=DEBUG
python -m zap_custom_mcp
```

### Connection Issues

```bash
# Check if ZAP is running
curl http://localhost:8080/JSON/core/view/version/

# Check MCP server
curl http://localhost:8082/mcp

# Check firewall settings
```

### MCP Client Connection Issues

If your MCP client cannot connect:

1. Ensure the server has been running for at least 90 seconds
2. Verify the URL is correct: `http://localhost:8082/mcp`
3. Check that no firewall is blocking port 8082
4. For Cursor IDE, ensure your `mcp.json` configuration is correct

### Container Issues

**📖 For detailed container troubleshooting, see:**
- **[DOCKER.md](DOCKER.md)** - Docker troubleshooting guide
- **[PODMAN.md](PODMAN.md)** - Podman troubleshooting guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install development dependencies: `pip install -e ".[dev]"`
4. Run tests: `pytest`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/LisBerndt/zap-custom-mcp.git
cd zap-custom-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Start development server
python -m zap_custom_mcp
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OWASP ZAP](https://www.zaproxy.org/) - The amazing security testing tool
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes AI integration possible
- [Sovereign Engineering](https://sovereignengineering.io/) - SEC-05 cohort for inspiring freedom tech and self-sovereign applications

### Special Thanks

This project was inspired by the **Sovereign Engineering Community** and their commitment to building tools for a self-sovereign future. The SEC-05 cohort's dedication to freedom tech, censorship resistance, and permissionless access aligns perfectly with the goals of making security testing tools more accessible and decentralized.

_"Build applications and services for a self-sovereign future."_ — [Sovereign Engineering](https://sovereignengineering.io/)

## 📞 Support

- 📖 [Documentation](https://github.com/LisBerndt/zap-custom-mcp/wiki)
- 🐛 [Issue Tracker](https://github.com/LisBerndt/zap-custom-mcp/issues)
- 💬 [Discussions](https://github.com/LisBerndt/zap-custom-mcp/discussions)

---

**Vibe coded with ❤️ for the self sovereign engineer - YOLO!**
