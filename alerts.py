import sys
from pathlib import Path
from typing import Any, Dict, List

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from http_session import get_json

_DEFAULT_ALERT_COUNTS = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}


def count_alerts_by_risk(alerts: List[dict]) -> Dict[str, int]:
    counts = _DEFAULT_ALERT_COUNTS.copy()
    for alert in alerts:
        risk = (alert.get("risk") or alert.get("riskdesc", "Informational")).split()[0]
        counts[risk if risk in counts else "Informational"] += 1
    return counts


def alerts_summary_fast(scan_id: str, baseurl: str, session_id=None) -> Dict[str, Any]:
    try:
        data = get_json(
            scan_id,
            "/JSON/core/view/alertsSummary/",
            {"baseurl": baseurl},
            session_id=session_id,
        )
        counts = _DEFAULT_ALERT_COUNTS.copy()
        items = (
            data.get("alertsSummary")
            or data.get("summary")
            or data.get("alerts-summary")
            or []
        )
        if isinstance(items, list):
            for item in items:
                risk = (
                    item.get("risk") or item.get("riskdesc", "Informational")
                ).split()[0]
                cnt = int(item.get("count", item.get("number", 0)))
                counts[risk if risk in counts else "Informational"] += cnt
        elif isinstance(items, dict):
            for k, v in items.items():
                risk = str(k).split()[0].title()
                counts[risk if risk in counts else "Informational"] += int(v)
        return {"counts": counts, "total": sum(counts.values())}
    except Exception:
        pass

    try:
        data = get_json(
            scan_id,
            "/JSON/core/view/alerts/",
            {"baseurl": baseurl, "start": 0, "count": 500},
            session_id=session_id,
        )
        alerts = data.get("alerts", [])
        counts = count_alerts_by_risk(alerts)
        return {"counts": counts, "total": sum(counts.values())}
    except Exception:
        pass

    try:
        num = get_json(
            scan_id,
            "/JSON/core/view/numberOfAlerts/",
            {"baseurl": baseurl},
            session_id=session_id,
        ).get("numberOfAlerts")
        total = int(num) if num is not None else 0
    except Exception:
        total = 0

    counts = _DEFAULT_ALERT_COUNTS.copy()
    counts["Informational"] = total
    return {"counts": counts, "total": total}


def alerts_page(
    scan_id: str, baseurl: str, start: int, count: int, session_id=None
) -> List[dict]:
    data = get_json(
        scan_id,
        "/JSON/core/view/alerts/",
        {"baseurl": baseurl, "start": start, "count": count},
        session_id=session_id,
    )
    return data.get("alerts", []) or []


def format_alert(alert: dict, include_evidence: bool) -> dict:
    entry = {
        "risk": alert.get("risk"),
        "alert": alert.get("alert"),
        "url": alert.get("url"),
        "param": alert.get("param"),
    }
    if include_evidence:
        entry["evidence"] = alert.get("evidence")
    return entry


def alerts_all(
    scan_id: str, baseurl: str, include_evidence: bool, session_id=None
) -> List[dict]:
    alerts = []
    start = 0
    page_size = 500
    while True:
        batch = alerts_page(scan_id, baseurl, start, page_size, session_id=session_id)
        if not batch:
            break
        alerts.extend([format_alert(alert, include_evidence) for alert in batch])
        start += page_size
    return alerts
