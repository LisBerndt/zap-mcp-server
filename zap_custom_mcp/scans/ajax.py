import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel

# Add the parent directory to the path to fix imports
sys.path.append(str(Path(__file__).parent.parent))

from http_session import get_json
from logging_setup import setup_logger

LOG = setup_logger("zap_mcp.scans.ajax")


class AjaxOptions(BaseModel):
    inScope: bool = False
    subtreeOnly: bool = True
    maxCrawlDepth: int = 10
    maxCrawlStates: int = 0  # 0 = unlimited (ZAP default)
    maxDuration: int = 60  # Minuten
    eventWait: int = 1000  # ms
    reloadWait: int = 1000  # ms
    clickDefaultElems: bool = True
    clickElemsOnce: bool = True
    numberOfBrowsers: int = 1  # parallel running browser instances
    browserId: Optional[str] = (
        "firefox-headless"  # Firefox Headless as default, can be explicitly overridden
    )
    wait_seconds: int = 300
    poll_interval_seconds: float = 1.0


def run_ajax(
    scan_id: str, target: str, a: AjaxOptions, session_id: str
) -> Tuple[bool, float, int]:
    def set_opt(path: str, param_name: str, value):
        if value is None:
            return
        get_json(
            scan_id,
            path,
            {param_name: str(value).lower() if isinstance(value, bool) else value},
            session_id=session_id,
        )

    # Determine browser: Firefox Headless as default
    browser_id = a.browserId or "firefox-headless"
    LOG.info(
        f"Using browser: {browser_id}",
        extra={"extra": {"scan_id": scan_id, "browser_id": browser_id}},
    )

    # Browser ID is already set in complete_flow(), so only log here
    LOG.info(
        f"AJAX Spider uses browser: {browser_id} (already configured)",
        extra={"extra": {"scan_id": scan_id, "browser_id": browser_id}},
    )

    # Set AJAX options (before start)
    set_opt(
        "/JSON/ajaxSpider/action/setOptionMaxCrawlDepth/", "Integer", a.maxCrawlDepth
    )
    set_opt(
        "/JSON/ajaxSpider/action/setOptionMaxCrawlStates/", "Integer", a.maxCrawlStates
    )
    set_opt("/JSON/ajaxSpider/action/setOptionMaxDuration/", "Integer", a.maxDuration)
    set_opt("/JSON/ajaxSpider/action/setOptionEventWait/", "Integer", a.eventWait)
    set_opt("/JSON/ajaxSpider/action/setOptionReloadWait/", "Integer", a.reloadWait)
    set_opt(
        "/JSON/ajaxSpider/action/setOptionClickDefaultElems/",
        "Boolean",
        a.clickDefaultElems,
    )
    set_opt(
        "/JSON/ajaxSpider/action/setOptionClickElemsOnce/", "Boolean", a.clickElemsOnce
    )
    set_opt(
        "/JSON/ajaxSpider/action/setOptionNumberOfBrowsers/",
        "Integer",
        a.numberOfBrowsers,
    )

    params: Dict[str, Any] = {
        "url": target,
        "inScope": "false",  # Hardcoded to false
        "subtreeOnly": "true",  # Hardcoded to true
    }

    t0 = time.monotonic()
    try:
        # AJAX Spider uses the correct scan endpoint
        get_json(
            scan_id, "/JSON/ajaxSpider/action/scan/", params, session_id=session_id
        )
    except Exception as e:
        LOG.error(
            "ajax.start.error", extra={"extra": {"scan_id": scan_id, "err": repr(e)}}
        )
        return (False, 0.0, 0)

    status = ""
    results = 0
    deadline = time.monotonic() + a.wait_seconds

    while time.monotonic() < deadline:
        try:
            status = (
                get_json(
                    scan_id, "/JSON/ajaxSpider/view/status/", {}, session_id=session_id
                )
                .get("status", "")
                .lower()
            )
            nr = get_json(
                scan_id,
                "/JSON/ajaxSpider/view/numberOfResults/",
                {},
                session_id=session_id,
            ).get("numberOfResults")
            results = int(nr) if nr is not None else results
        except Exception:
            pass
        if status in ("stopped", "complete", "finished"):
            break
        time.sleep(max(0.2, a.poll_interval_seconds))

    if status not in ("stopped", "complete", "finished"):
        try:
            get_json(
                scan_id, "/JSON/ajaxSpider/action/stop/", {}, session_id=session_id
            )
        except Exception:
            pass

    duration = round(time.monotonic() - t0, 2)
    return (True, duration, results)
