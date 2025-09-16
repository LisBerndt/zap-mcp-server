import sys
import time
from pathlib import Path
from typing import Dict

# Add the parent directory to the path to fix imports
sys.path.append(str(Path(__file__).parent.parent))

from alerts import alerts_all, alerts_summary_fast
from config import MCP_SAY
from logging_setup import setup_logger
from utils import canonical_base
from zap_control import ensure_session, ensure_zap_running

LOG = setup_logger("zap_mcp.scan.passive")


def pscan_wait(
    scan_id: str, interval_s: float, timeout_s: int, session_id: str
) -> float:
    from http_session import get_json

    start = time.monotonic()
    last_log = start

    while True:
        remaining = 0
        try:
            data = get_json(
                scan_id, "/JSON/pscan/view/recordsToScan/", {}, session_id=session_id
            )
            remaining = int(data.get("recordsToScan", "0"))
        except Exception:
            break
        now = time.monotonic()
        if now - last_log >= max(1.0, interval_s * 4):
            LOG.info(
                "pscan.queue",
                extra={"extra": {"scan_id": scan_id, "remaining": remaining}},
            )
            last_log = now
        if remaining <= 0:
            break
        if now - start > timeout_s:
            LOG.warning(
                "pscan.timeout",
                extra={"extra": {"scan_id": scan_id, "remaining": remaining}},
            )
            break
        time.sleep(interval_s)
    return round(time.monotonic() - start, 2)


def passive_scan_impl(
    scan_id: str,
    target: str,
    include_findings: bool,
    include_evidence: bool,
    session_id: str,
) -> Dict:
    base_for_alerts = canonical_base(target)
    summary = alerts_summary_fast(scan_id, base_for_alerts, session_id=session_id)
    findings = (
        alerts_all(scan_id, base_for_alerts, include_evidence, session_id=session_id)
        if include_findings
        else []
    )
    return {"summary": summary, "findings": findings}
