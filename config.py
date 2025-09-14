import os

# Docker Detection and Configuration
def is_docker_environment():
    """Check if running in Docker container"""
    return os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'

def apply_docker_config():
    """Apply Docker-specific configuration"""
    if is_docker_environment():
        os.environ.setdefault("ZAP_BASE", "http://127.0.0.1:8080")
        os.environ.setdefault("ZAP_AUTOSTART", "false")  # ZAP is started by entrypoint
        os.environ.setdefault("ZAP_MCP_HOST", "0.0.0.0")  # Listen on all interfaces
        os.environ.setdefault("ZAP_SESSION_NAME", "zap_docker_session")
        os.environ.setdefault("ZAP_SESSION_STRATEGY", "unique")
        os.environ.setdefault("ZAP_STARTUP_TIMEOUT", "120")
        os.environ.setdefault("ZAP_LONG_SCAN_TIMEOUT", "14400")
        os.environ.setdefault("ZAP_LOG_LEVEL", "INFO")

# Apply Docker config when module is imported
apply_docker_config()

# MCP Server Configuration
MCP_HOST = os.environ.get("ZAP_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("ZAP_MCP_PORT", "8082"))
MCP_PATH = os.environ.get("ZAP_MCP_PATH", "/mcp")

# ZAP Configuration
ZAP_BASE = os.environ.get("ZAP_BASE", "http://127.0.0.1:8080")
APIKEY = os.environ.get("ZAP_APIKEY", "")

# ZAP Autostart Configuration
ZAP_AUTOSTART = os.environ.get("ZAP_AUTOSTART", "true").lower() in ("1", "true", "yes")
# ZAP_PATH is no longer needed as zap.bat should be available in PATH
ZAP_STARTUP_TIMEOUT = int(os.environ.get("ZAP_STARTUP_TIMEOUT", "60"))
ZAP_STARTUP_POLL = float(os.environ.get("ZAP_STARTUP_POLL", "1.0"))

# Session Configuration
SESSION_NAME = os.environ.get("ZAP_SESSION_NAME", "zap_mcp_session")
SESSION_STRATEGY = os.environ.get("ZAP_SESSION_STRATEGY", "unique")  # reuse, unique, new

# HTTP Configuration
RETRY_TOTAL = int(os.environ.get("ZAP_RETRY_TOTAL", "5"))  # Increased from 3 to 5
RETRY_CONNECT = int(os.environ.get("ZAP_RETRY_CONNECT", "3"))  # Increased from 2 to 3
RETRY_READ = int(os.environ.get("ZAP_RETRY_READ", "3"))  # Increased from 2 to 3
BACKOFF = float(os.environ.get("ZAP_BACKOFF", "1.0"))  # Increased from 0.5 to 1.0

# Logging Configuration
RESP_PREVIEW = int(os.environ.get("ZAP_RESP_PREVIEW", "200"))
LOG_PARAMS = os.environ.get("ZAP_LOG_PARAMS", "false").lower() in ("1", "true", "yes")

# Progress Configuration
PROGRESS_STEP = int(os.environ.get("ZAP_PROGRESS_STEP", "10"))

# MCP Say Configuration (for notifications)
MCP_SAY = os.environ.get("ZAP_MCP_SAY", "false").lower() in ("1", "true", "yes")

# Long-running operation timeouts
LONG_SCAN_TIMEOUT = int(os.environ.get("ZAP_LONG_SCAN_TIMEOUT", "14400"))  # 4 hours default

# MCP Server timeout configuration
MCP_SERVER_TIMEOUT = int(os.environ.get("ZAP_MCP_SERVER_TIMEOUT", "300"))  # 5 minutes default
MCP_HEARTBEAT_INTERVAL = int(os.environ.get("ZAP_MCP_HEARTBEAT_INTERVAL", "30"))  # 30 seconds default

# Scan-specific timeout overrides
DEFAULT_ACTIVE_SCAN_TIMEOUT = int(os.environ.get("ZAP_DEFAULT_ACTIVE_SCAN_TIMEOUT", "7200"))  # 2 hours
DEFAULT_SPIDER_TIMEOUT = int(os.environ.get("ZAP_DEFAULT_SPIDER_TIMEOUT", "1800"))  # 30 minutes
DEFAULT_AJAX_TIMEOUT = int(os.environ.get("ZAP_DEFAULT_AJAX_TIMEOUT", "300"))  # 5 minutes
DEFAULT_PASSIVE_TIMEOUT = int(os.environ.get("ZAP_DEFAULT_PASSIVE_TIMEOUT", "600"))  # 10 minutes

# HTTP timeout configuration
HTTP_CONNECT_TIMEOUT = int(os.environ.get("ZAP_HTTP_CONNECT_TIMEOUT", "30"))  # 30 seconds
HTTP_READ_TIMEOUT = int(os.environ.get("ZAP_HTTP_READ_TIMEOUT", "600"))  # 10 minutes
HTTP_POOL_SIZE = int(os.environ.get("ZAP_HTTP_POOL_SIZE", "50"))  # Connection pool size  # 4 hours for long scans
