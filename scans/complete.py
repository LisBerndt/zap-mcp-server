import uuid
from typing import Dict

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alerts import alerts_all, alerts_summary_fast
from utils import canonical_base, vuln_names_from_findings
from config import MCP_SAY
from zap_control import ensure_zap_running, ensure_session, access_url
from scans.ajax import AjaxOptions, run_ajax
from scans.spider import run_spider
from scans.active import run_ascan
from http_session import get_json
from logging_setup import setup_logger


def complete_flow(scan_id: str, target: str, args, session_id: str) -> Dict:
    LOG = setup_logger("zap_mcp.scans.complete")
    
    # 0. Set browser configuration BEFORE starting scans
    browser_id = getattr(args, 'ajax_browserId', None) or "firefox-headless"
    try:
        get_json(
            scan_id,
            "/JSON/ajaxSpider/action/setOptionBrowserId/",
            {"String": browser_id},
            session_id=session_id,
        )
        LOG.info(
            f"Browser configuration set BEFORE scan start: {browser_id}",
            extra={"extra": {"scan_id": scan_id, "browser_id": browser_id}},
        )
    except Exception as e:
        LOG.warning(
            f"Browser configuration failed: {e}. Scan will continue...",
            extra={"extra": {"scan_id": scan_id, "browser_id": browser_id}},
        )
    
    # 1. Traditional Spider (first)
    spider_id, spider_duration = run_spider(scan_id, target, args.recurse, args.inScopeOnly, args.poll_interval_seconds, args.spider_max_wait_seconds, session_id=session_id)

    # 2. AJAX Spider (after traditional spider)
    ajax_opts = AjaxOptions(
        inScope=False,  # Explicitly set to False
        subtreeOnly=True,  # Explicitly set to True
        maxCrawlDepth=args.ajax_maxCrawlDepth,
        maxCrawlStates=args.ajax_maxCrawlStates,
        maxDuration=args.ajax_maxDuration,
        eventWait=args.ajax_eventWait,
        clickDefaultElems=args.ajax_clickDefaultElems,
        clickElemsOnce=args.ajax_clickElemsOnce,
        browserId=args.ajax_browserId,
        wait_seconds=args.ajax_wait_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    ajax_ok, ajax_duration, ajax_results = run_ajax(scan_id, target, ajax_opts, session_id=session_id)

    # 3. Passive scan (runs automatically in parallel, but we wait for it)
    from scans.passive import pscan_wait
    pscan_duration = pscan_wait(scan_id, args.passive_poll_interval_seconds, args.passive_timeout_seconds, session_id=session_id)

    # 4. Active scan (last)
    ascan_id, ascan_duration = run_ascan(scan_id, target, args.recurse, args.inScopeOnly, args.scanPolicyName, args.poll_interval_seconds, args.ascan_max_wait_seconds, session_id=session_id)

    return {
        "spider": {"id": spider_id, "duration": round(spider_duration, 2)},
        "ajax": {"ok": ajax_ok, "duration": round(ajax_duration, 2), "results": ajax_results},
        "passiveScan": {"duration": round(pscan_duration, 2)},
        "ascan": {"id": ascan_id, "duration": round(ascan_duration, 2)},
    }