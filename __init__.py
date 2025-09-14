import os

ZAP_BASE = os.environ.get("ZAP_URL", "http://127.0.0.1:8080").rstrip("/")
APIKEY = os.environ.get("ZAP_APIKEY", "").strip()
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8082"))
MCP_PATH = os.environ.get("MCP_PATH", "/mcp")

SESSION_NAME = os.environ.get("ZAP_SESSION_NAME", "mcp_session").strip()
SESSION_STRATEGY = os.environ.get("ZAP_SESSION_STRATEGY", "unique").strip().lower()

DISABLE_WEBSOCKET = os.environ.get("ZAP_DISABLE_WEBSOCKET", "0").lower() in (
    "1",
    "true",
    "yes",
)

LOG_PARAMS = os.environ.get("ZAP_MCP_LOG_PARAMS", "1").lower() in ("1", "true", "yes")
RESP_PREVIEW = int(os.environ.get("ZAP_MCP_LOG_RESP_PREVIEW", "200"))
PROGRESS_STEP = max(1, min(50, int(os.environ.get("ZAP_MCP_PROGRESS_STEP", "10"))))

RETRY_TOTAL = int(os.environ.get("ZAP_MCP_RETRY_TOTAL", "5"))
RETRY_CONNECT = int(os.environ.get("ZAP_MCP_RETRY_CONNECT", "3"))
RETRY_READ = int(os.environ.get("ZAP_MCP_RETRY_READ", "3"))
BACKOFF = float(os.environ.get("ZAP_MCP_BACKOFF", "0.5"))

MCP_SAY = os.environ.get("ZAP_MCP_SAY", "1").lower() in ("1", "true", "yes")

ZAP_AUTOSTART = os.environ.get("ZAP_AUTOSTART", "1").lower() in ("1", "true", "yes")
ZAP_PATH = os.environ.get("ZAP_PATH", r"C:\Program Files\ZAP\Zed Attack Proxy").strip()
ZAP_STARTUP_TIMEOUT = int(os.environ.get("ZAP_STARTUP_TIMEOUT_SECS", "120"))
ZAP_STARTUP_POLL = float(os.environ.get("ZAP_STARTUP_POLL_INTERVAL", "1.0"))
