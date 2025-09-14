import time
from typing import Optional, Tuple

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from http_session import get_json
from config import PROGRESS_STEP
from logging_setup import setup_logger

LOG = setup_logger("zap_mcp.scans.active")


def run_ascan(
    scan_id: str,
    target: str,
    recurse: bool,
    in_scope_only: bool,
    scan_policy: Optional[str],
    poll_s: float,
    max_wait_s: int,
    session_id: str,
    progress_callback: Optional[callable] = None,
) -> Tuple[str, float]:
    ascan_resp = get_json(
        scan_id,
        "/JSON/ascan/action/scan/",
        {
            "url": target,
            "recurse": str(recurse).lower(),
            "inScopeOnly": str(in_scope_only).lower(),
            "scanPolicyName": scan_policy,
        },
        session_id=session_id,
    )

    ascan_id = (
        ascan_resp.get("scan")
        or ascan_resp.get("scanid")
        or ascan_resp.get("scanId")
        or "0"
    )
    LOG.info(
        "ascan.started",
        extra={
            "extra": {
                "scan_id": scan_id,
                "id": ascan_id,
                "recurse": recurse,
                "inScopeOnly": in_scope_only,
                "policy": scan_policy,
            }
        },
    )

    start = time.monotonic()
    last_logged = -1

    while True:
        try:
            status = get_json(
                scan_id,
                "/JSON/ascan/view/status/",
                {"scanId": str(ascan_id)},
                session_id=session_id,
            ).get("status")
        except Exception as e:
            LOG.warning(
                "ascan.poll.transient",
                extra={"extra": {"scan_id": scan_id, "err": repr(e)}},
            )
            time.sleep(min(3.0, max(1.0, poll_s * 2)))
            if time.monotonic() - start > max_wait_s:
                raise TimeoutError("Active scan timeout")
            continue

        try:
            pct = int(status)
        except Exception:
            pct = 0

        now = time.monotonic()

        if pct // PROGRESS_STEP != last_logged // PROGRESS_STEP:
            LOG.info(
                "ascan.progress",
                extra={"extra": {"scan_id": scan_id, "id": ascan_id, "status": pct}},
            )
            last_logged = pct
            
            # Call progress callback if provided
            if progress_callback:
                try:
                    progress_callback(scan_id, "active", pct, f"Active scan progress: {pct}%")
                except Exception as e:
                    LOG.warning(f"Progress callback failed: {e}")

        if str(status) == "100":
            break

        if now - start > max_wait_s:
            raise TimeoutError("Active scan timeout")

        time.sleep(poll_s)

    duration = time.monotonic() - start
    return str(ascan_id), duration
