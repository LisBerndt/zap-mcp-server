import os
import time
import subprocess
from typing import Optional
from urllib.parse import urlparse

import requests

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    ZAP_BASE, ZAP_AUTOSTART, ZAP_STARTUP_TIMEOUT, 
    ZAP_STARTUP_POLL, SESSION_NAME, SESSION_STRATEGY
)
from logging_setup import setup_logger
from http_session import get_json

LOG = setup_logger("zap_mcp.zap_control")
ZAP_SESSION_ID: Optional[str] = None


def zap_is_running() -> bool:
    try:
        url = f"{ZAP_BASE}/JSON/core/view/version/"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            LOG.debug("zap.api.accessible", extra={"extra": {"url": url, "status": r.status_code}})
            return True
        else:
            LOG.debug("zap.api.inaccessible", extra={"extra": {"url": url, "status": r.status_code}})
            return False
    except Exception as e:
        LOG.debug("zap.api.error", extra={"extra": {"url": url, "error": repr(e)}})
        return False


def _find_zap_directory() -> Optional[str]:
    """Find the ZAP installation directory by locating zap.bat"""
    try:
        result = subprocess.run(['where', 'zap.bat'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            zap_bat_path = result.stdout.strip().split('\n')[0]
            # Get the directory containing zap.bat
            zap_dir = os.path.dirname(zap_bat_path)
            return zap_dir
    except Exception:
        pass
    return None


def _check_zap_ports() -> list:
    """Check common ZAP ports to see if ZAP is running"""
    common_ports = [8080, 8081, 8082, 8083, 8084, 8085]
    running_ports = []
    
    for port in common_ports:
        try:
            url = f"http://127.0.0.1:{port}/JSON/core/view/version/"
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                running_ports.append(port)
                LOG.info("zap.found.on.port", extra={"extra": {"port": port}})
        except Exception:
            continue
    
    return running_ports


def _build_zap_cmd(zap_dir: str) -> str:
    p = urlparse(ZAP_BASE)
    host = p.hostname or "127.0.0.1"
    port = p.port or (443 if p.scheme == "https" else 8080)
    # Use cmd /c with proper working directory
    return f'cmd /c "cd /d "{zap_dir}" && zap.bat -daemon -port {port} -host {host} -config api.disablekey=true"'


def ensure_zap_running() -> None:
    p = urlparse(ZAP_BASE)
    host = (p.hostname or "").lower()
    is_local = host in ("127.0.0.1", "localhost")

    if not is_local:
        LOG.info("zap.autostart.skip.remote", extra={"extra": {"host": host}})
        return

    if zap_is_running():
        LOG.info("zap.detected.running")
        return
    
    # Check if ZAP is running on other ports
    running_ports = _check_zap_ports()
    if running_ports:
        LOG.info("zap.detected.on.alternate.port", extra={"extra": {"ports": running_ports}})
        return

    if not ZAP_AUTOSTART:
        LOG.warning("zap.autostart.disabled")
        return

    if os.name != "nt":
        LOG.warning("zap.autostart.skip.non_windows")
        return

    zap_dir = _find_zap_directory()
    if not zap_dir:
        LOG.error("zap.autostart.not_in_path", extra={"extra": {"message": "zap.bat not found in PATH"}})
        return

    cmd = _build_zap_cmd(zap_dir)

    LOG.info("zap.autostart.exec", extra={"extra": {"cmd": cmd}})
    try:
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        LOG.error("zap.autostart.spawn_failed", extra={"extra": {"err": repr(e)}})
        return

    t0 = time.monotonic()
    while time.monotonic() - t0 < ZAP_STARTUP_TIMEOUT:
        if zap_is_running():
            LOG.info("zap.autostart.ready")
            return
        time.sleep(max(0.25, ZAP_STARTUP_POLL))

    LOG.error("zap.autostart.timeout", extra={"extra": {"timeout_s": ZAP_STARTUP_TIMEOUT}})


def ensure_session() -> Optional[str]:
    global ZAP_SESSION_ID
    if ZAP_SESSION_ID:
        return ZAP_SESSION_ID

    name = SESSION_NAME
    if SESSION_STRATEGY == "unique":
        name = f"{SESSION_NAME}_{int(time.time())}"

    def _params(extra=None):
        p = {"name": name}
        if extra:
            p.update(extra)
        return p

    try:
        if SESSION_STRATEGY in ("reuse", "unique"):
            r = requests.get(f"{ZAP_BASE}/JSON/core/action/loadSession/", params=_params())
            if r.status_code == 200:
                ZAP_SESSION_ID = name
                return ZAP_SESSION_ID
    except Exception:
        pass

    for params in (_params(), _params({"overwrite": "true"})):
        try:
            r = requests.get(f"{ZAP_BASE}/JSON/core/action/newSession/", params=params)
            if r.status_code == 200:
                ZAP_SESSION_ID = name
                return ZAP_SESSION_ID
        except Exception:
            continue

    return None


def access_url(scan_id: str, url: str, follow_redirects: bool = True):
    try:
        get_json(scan_id, "/JSON/core/action/accessUrl/", {"url": url, "followRedirects": str(follow_redirects).lower()}, session_id=ZAP_SESSION_ID)
    except Exception as e:
        LOG.warning("accessUrl.warn", extra={"extra": {"scan_id": scan_id, "err": repr(e)}})