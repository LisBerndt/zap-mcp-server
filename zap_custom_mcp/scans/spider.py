import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from ..config import PROGRESS_STEP
from ..http_session import get_json
from ..logging_setup import setup_logger

LOG = setup_logger("zap_mcp.scan.spider")


def run_spider(
    scan_id: str,
    target: str,
    recurse: bool,
    in_scope_only: bool,
    poll_s: float,
    max_wait_s: int,
    session_id: str,
    progress_callback: Optional[callable] = None,
) -> Tuple[str, float]:
    LOG.info(
        f"Starting spider scan",
        extra={
            "extra": {
                "scan_id": scan_id,
                "target": target,
                "recurse": recurse,
                "in_scope_only": in_scope_only,
                "poll_s": poll_s,
                "max_wait_s": max_wait_s,
            }
        },
    )

    spider_resp = get_json(
        scan_id, "/JSON/spider/action/scan/", {"url": target}, session_id=session_id
    )
    spider_id = (
        spider_resp.get("scan")
        or spider_resp.get("scanid")
        or spider_resp.get("scanId")
        or "0"
    )

    LOG.info(
        f"Spider scan started",
        extra={
            "extra": {
                "scan_id": scan_id,
                "spider_id": spider_id,
                "target": target,
                "response": spider_resp,
            }
        },
    )

    t0 = time.monotonic()
    start = time.monotonic()
    last_logged = -1
    consecutive_errors = 0
    max_consecutive_errors = 20
    stuck_progress_count = 0
    last_progress = -1

    while True:
        try:
            LOG.debug(
                f"Checking spider status",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "spider_id": spider_id,
                        "consecutive_errors": consecutive_errors,
                        "stuck_count": stuck_progress_count,
                    }
                },
            )
            status = get_json(
                scan_id,
                "/JSON/spider/view/status/",
                {"scanId": str(spider_id)},
                timeout=600,
                session_id=session_id,
            ).get("status")
            consecutive_errors = 0
            LOG.debug(
                f"Spider status check successful",
                extra={"extra": {"scan_id": scan_id, "status": status}},
            )
        except Exception as e:
            consecutive_errors += 1
            LOG.error(
                f"Spider status check failed",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "spider_id": spider_id,
                        "consecutive_errors": consecutive_errors,
                        "error": str(e),
                    }
                },
            )

            if consecutive_errors >= max_consecutive_errors:
                LOG.error(
                    f"Too many consecutive errors, giving up",
                    extra={
                        "extra": {
                            "scan_id": scan_id,
                            "consecutive_errors": consecutive_errors,
                        }
                    },
                )
                raise TimeoutError(
                    f"Spider failed after {consecutive_errors} consecutive errors: {str(e)}"
                )

            error_sleep = min(30.0, poll_s * 1.5**consecutive_errors)
            LOG.warning(
                f"Sleeping after error",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "error_sleep": error_sleep,
                        "consecutive_errors": consecutive_errors,
                    }
                },
            )
            time.sleep(error_sleep)

            if time.monotonic() - start > max_wait_s:
                LOG.error(
                    f"Spider timeout exceeded",
                    extra={
                        "extra": {
                            "scan_id": scan_id,
                            "elapsed": time.monotonic() - start,
                            "max_wait": max_wait_s,
                        }
                    },
                )
                raise TimeoutError("Spider timeout")
            continue

        try:
            pct = int(status)
        except Exception:
            pct = 0

        now = time.monotonic()

        # Check if progress is stuck
        if pct == last_progress:
            stuck_progress_count += 1
            LOG.debug(
                f"Spider progress stuck",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "progress": pct,
                        "stuck_count": stuck_progress_count,
                    }
                },
            )
        else:
            stuck_progress_count = 0
            last_progress = pct
            LOG.info(
                f"Spider progress updated",
                extra={"extra": {"scan_id": scan_id, "progress": pct}},
            )

        # If stuck for too long, extend polling interval
        if stuck_progress_count > 10:
            extended_poll = min(30.0, poll_s * 2)
            LOG.warning(
                f"Spider progress stuck, extending poll interval",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "progress": pct,
                        "stuck_count": stuck_progress_count,
                        "extended_poll": extended_poll,
                    }
                },
            )
            time.sleep(extended_poll)
            continue

        if pct // PROGRESS_STEP != last_logged // PROGRESS_STEP:
            last_logged = pct
            LOG.info(
                f"Spider progress milestone",
                extra={"extra": {"scan_id": scan_id, "progress": pct}},
            )

            # Call progress callback if provided
            if progress_callback:
                try:
                    progress_callback(
                        scan_id, "spider", pct, f"Spider scan progress: {pct}%"
                    )
                except Exception as e:
                    LOG.warning(f"Progress callback failed: {e}")

        if str(status) == "100":
            LOG.info(
                f"Spider completed",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "spider_id": spider_id,
                        "duration": time.monotonic() - start,
                    }
                },
            )
            break

        if now - start > max_wait_s:
            LOG.error(
                f"Spider timeout",
                extra={
                    "extra": {
                        "scan_id": scan_id,
                        "elapsed": now - start,
                        "max_wait": max_wait_s,
                    }
                },
            )
            raise TimeoutError("Spider timeout")

        time.sleep(poll_s)

    duration = time.monotonic() - t0
    LOG.info(
        f"Spider scan finished",
        extra={
            "extra": {"scan_id": scan_id, "spider_id": spider_id, "duration": duration}
        },
    )
    return str(spider_id), duration
