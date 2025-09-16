from typing import Any, Mapping, Optional, Union

from pydantic import BaseModel, HttpUrl


class BaseScanArgs(BaseModel):
    url: HttpUrl
    followRedirects: bool = True
    recurse: bool = True
    inScopeOnly: bool = False
    scanPolicyName: Optional[str] = None
    poll_interval_seconds: float = 1.5
    include_findings: bool = True
    include_evidence: bool = False


class PassiveScanArgs(BaseScanArgs):
    passive_only_in_scope: Optional[bool] = None
    wait_for_passive: bool = True
    passive_poll_interval_seconds: float = 0.5
    passive_timeout_seconds: int = 600


class AjaxScanArgs(BaseScanArgs):
    ajax_inScope: bool = True
    ajax_subtreeOnly: bool = False
    ajax_maxCrawlDepth: int = 10
    ajax_maxCrawlStates: int = 0
    ajax_maxDuration: int = 60
    ajax_eventWait: int = 1000
    ajax_clickDefaultElems: bool = True
    ajax_clickElemsOnce: bool = True
    ajax_browserId: Optional[str] = None
    ajax_wait_seconds: int = 300


class SpiderScanArgs(BaseScanArgs):
    spider_max_wait_seconds: int = 1800


class ActiveScanArgs(SpiderScanArgs):
    ascan_max_wait_seconds: int = 7200


class CompleteScanArgs(ActiveScanArgs, AjaxScanArgs, PassiveScanArgs):
    disable_websocket: bool = False
