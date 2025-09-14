import time
import random
import urllib.parse
from typing import Dict, Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ZAP_BASE, APIKEY, RETRY_TOTAL, RETRY_CONNECT, RETRY_READ, 
    BACKOFF, RESP_PREVIEW, LOG_PARAMS, HTTP_CONNECT_TIMEOUT, 
    HTTP_READ_TIMEOUT, HTTP_POOL_SIZE
)
from logging_setup import setup_logger

LOG = setup_logger("zap_mcp.http_session")
_REQ_SESSION = None


class TimeoutHTTPAdapter(HTTPAdapter):
    """Custom HTTPAdapter with explicit connection and read timeouts"""
    
    def __init__(self, *args, **kwargs):
        self.connect_timeout = kwargs.pop('connect_timeout', 30)
        self.read_timeout = kwargs.pop('read_timeout', 300)
        super().__init__(*args, **kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        kwargs['socket_options'] = [(6, 1, 1)]  # TCP_NODELAY
        return super().init_poolmanager(*args, **kwargs)
    
    def get_connection(self, url, proxies=None):
        conn = super().get_connection(url, proxies)
        conn.timeout = (self.connect_timeout, self.read_timeout)
        return conn


def _redact_params(params: Dict[str, Any]) -> Dict[str, Any]:
    out = params.copy()
    if "apikey" in out:
        out["apikey"] = "***"
    return out


def _log_api_call(scan_id: str, path: str, params: Dict[str, Any], status: Optional[int], elapsed: float, err: Optional[str], body_preview: Optional[str] = None):
    extra = {
        "scan_id": scan_id, 
        "path": path, 
        "status": status if status is not None else "n/a", 
        "elapsed_ms": int(elapsed * 1000),
        "timestamp": time.time()
    }
    if LOG_PARAMS:
        extra["params"] = _redact_params(params)
    if body_preview is not None and RESP_PREVIEW > 0:
        extra["resp_preview"] = body_preview[:RESP_PREVIEW]
    if err:
        extra["error"] = err
        LOG.error("zap_api_call error", extra={"extra": extra})
    else:
        LOG.info("zap_api_call ok", extra={"extra": extra})


def get_requests_session() -> requests.Session:
    global _REQ_SESSION
    if _REQ_SESSION:
        return _REQ_SESSION
    s = requests.Session()
    retry = Retry(
        total=RETRY_TOTAL,
        connect=RETRY_CONNECT,
        read=RETRY_READ,
        backoff_factor=BACKOFF,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    # Increased pool size and connection timeout for better reliability during long scans
    # CRITICAL: Use custom adapter with explicit connection and read timeouts to prevent 5-minute timeouts
    adapter = TimeoutHTTPAdapter(
        max_retries=retry, 
        pool_connections=HTTP_POOL_SIZE, 
        pool_maxsize=HTTP_POOL_SIZE, 
        pool_block=False,
        connect_timeout=HTTP_CONNECT_TIMEOUT,  # Configurable connection timeout
        read_timeout=HTTP_READ_TIMEOUT         # Configurable read timeout for long scans
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": "zap-mcp/1.1", "Accept": "application/json", "Connection": "keep-alive"})
    
    # Set default timeouts for the session - THIS IS CRITICAL!
    s.timeout = (HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT)  # (connect_timeout, read_timeout)
    
    _REQ_SESSION = s
    return s


def zap_url(path: str, params: Dict[str, Any], session_id: Optional[str]) -> str:
    base = f"{ZAP_BASE}{path}"
    q = {k: str(v) for k, v in params.items() if v is not None}
    if APIKEY:
        q["apikey"] = APIKEY
    if session_id:
        q["sessionId"] = session_id
    return base + "?" + urllib.parse.urlencode(q, doseq=True, safe="/:")


def http_get(scan_id: str, path: str, params: Dict[str, Any], timeout: int = 60, session_id: Optional[str] = None):
    url = zap_url(path, params, session_id)
    LOG.debug(f"HTTP GET request: {url[:100]}...", extra={"extra": {"scan_id": scan_id, "timeout": timeout, "session_id": session_id}})
    
    s = get_requests_session()
    for attempt in range(1, RETRY_TOTAL + 2):
        t0 = time.monotonic()
        r = None
        LOG.debug(f"HTTP attempt {attempt}/{RETRY_TOTAL + 1}", extra={"extra": {"scan_id": scan_id, "path": path}})
        
        try:
            r = s.get(url, timeout=timeout)
            elapsed = time.monotonic() - t0
            LOG.debug(f"HTTP response received", extra={"extra": {"scan_id": scan_id, "status": r.status_code, "elapsed_ms": int(elapsed * 1000)}})
            
            r.raise_for_status()
            preview = r.text[:RESP_PREVIEW] if RESP_PREVIEW > 0 else None
            _log_api_call(scan_id, path, params, r.status_code, elapsed, None, preview)
            return r
            
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError, requests.exceptions.ReadTimeout) as e:
            elapsed = time.monotonic() - t0
            status = getattr(r, "status_code", None)
            preview = r.text[:RESP_PREVIEW] if r is not None and RESP_PREVIEW > 0 else None
            LOG.error(f"HTTP connection error on attempt {attempt}", extra={"extra": {"scan_id": scan_id, "error": str(e), "elapsed_ms": int(elapsed * 1000)}})
            _log_api_call(scan_id, path, params, status, elapsed, f"{e.__class__.__name__}: {e}", preview)
            
            if attempt >= RETRY_TOTAL + 1:
                LOG.error(f"HTTP failed after {RETRY_TOTAL + 1} attempts", extra={"extra": {"scan_id": scan_id, "path": path}})
                raise
            sleep_s = min(6.0, BACKOFF * (2 ** (attempt - 1))) + random.uniform(0, 0.25)
            LOG.warning("http.retry", extra={"extra": {"scan_id": scan_id, "path": path, "attempt": attempt, "sleep_s": round(sleep_s, 2)}})
            time.sleep(sleep_s)
            
        except Exception as e:
            elapsed = time.monotonic() - t0
            status = getattr(r, "status_code", None)
            preview = r.text[:RESP_PREVIEW] if r is not None and RESP_PREVIEW > 0 else None
            LOG.error(f"HTTP unexpected error", extra={"extra": {"scan_id": scan_id, "error": str(e), "elapsed_ms": int(elapsed * 1000)}})
            _log_api_call(scan_id, path, params, status, elapsed, f"{e.__class__.__name__}: {e}", preview)
            raise


def get_json(scan_id: str, path: str, params: Dict[str, Any], timeout: int = 60, session_id: Optional[str] = None):
    return http_get(scan_id, path, params, timeout=timeout, session_id=session_id).json()


def get_text(scan_id: str, path: str, params: Dict[str, Any], timeout: int = 120, session_id: Optional[str] = None) -> str:
    return http_get(scan_id, path, params, timeout=timeout, session_id=session_id).text