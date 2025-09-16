import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse, urlunparse

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import PROGRESS_STEP

_RISK_LEVELS = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}
_RISK_WEIGHTS = {"High": 5, "Medium": 3, "Low": 1, "Informational": 0}


def canonical_base(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def sanitize_target(url: str) -> str:
    p = urlparse(url)
    path = (p.path or "/").replace("%23", "").replace("#", "")
    if not path or path == "//":
        path = "/"
    p = p._replace(fragment="", path=path)
    return urlunparse(p)


def transform_url_for_docker(url: str) -> str:
    """Transform URLs for Docker environment"""
    if not os.path.exists("/.dockerenv"):
        return url

    parsed = urlparse(url)

    # localhost/127.0.0.1 → host.docker.internal
    if parsed.hostname in ("localhost", "127.0.0.1"):
        new_hostname = "host.docker.internal"
        new_parsed = parsed._replace(
            netloc=f"{new_hostname}:{parsed.port}" if parsed.port else new_hostname
        )
        transformed_url = urlunparse(new_parsed)
        return transformed_url

    return url


def get_scan_url(url: str) -> str:
    """Get the correct URL for scans"""
    return transform_url_for_docker(url)


def vuln_names_from_findings(findings: List[dict]) -> List[dict]:
    if not findings:
        return []
    counter = Counter()
    for finding in findings:
        name = (finding.get("alert") or finding.get("name") or "").strip() or "Unknown"
        risk = (finding.get("risk") or "Informational").split()[0]
        counter[(risk, name)] += 1
    items = sorted(
        counter.items(),
        key=lambda kv: (_RISK_LEVELS.get(kv[0][0], 9), -kv[1], kv[0][1].lower()),
    )
    return [
        {"name": name, "risk": risk, "count": count} for (risk, name), count in items
    ]


def risk_score(counts: Dict[str, int]) -> int:
    return sum(int(counts.get(k, 0)) * w for k, w in _RISK_WEIGHTS.items())


def _prepare(scan_id: str, url: str) -> str:
    """Prepare target URL for scanning."""
    target = sanitize_target(url)
    from zap_control import access_url

    access_url(scan_id, target)
    return target


def _finalize(
    scan_id: str,
    target: str,
    include_findings: bool,
    include_evidence: bool,
    durations: Dict[str, float],
    mode: str,
) -> Dict:
    """Finalize scan results."""
    from alerts import alerts_all, alerts_summary_fast
    from zap_control import ZAP_SESSION_ID

    result = {
        "scanId": scan_id,
        "target": target,
        "mode": mode,
        "durations": durations,
        "total_duration_seconds": round(sum(durations.values()), 2),
    }

    if include_findings:
        summary = alerts_summary_fast(scan_id, target, session_id=ZAP_SESSION_ID)
        result["summary"] = summary

        if include_evidence:
            findings = alerts_all(
                scan_id, target, include_evidence=True, session_id=ZAP_SESSION_ID
            )
            result["findings"] = findings
            result["vulnerabilities"] = vuln_names_from_findings(findings)
            result["risk_score"] = risk_score(summary.get("counts", {}))

    return result
