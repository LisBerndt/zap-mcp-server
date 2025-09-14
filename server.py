import uuid
import sys
import asyncio
from pathlib import Path
from typing import Union, Dict, Any, Mapping
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from models import CompleteScanArgs
from scans.active import run_ascan
from scans.spider import run_spider
from scans.ajax import run_ajax, AjaxOptions
from scans.passive import passive_scan_impl
from utils import _prepare, _finalize
from zap_control import ZAP_SESSION_ID
from logging_setup import setup_logger

LOG = setup_logger("zap_mcp.server")

# Global scan management
class ScanManager:
    def __init__(self):
        self.active_scans: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="zap-scan")
        self.lock = threading.Lock()
    
    def start_scan(self, scan_id: str, scan_type: str, target: str, args: Dict[str, Any]) -> str:
        """Start a scan in background and return scan ID"""
        with self.lock:
            self.active_scans[scan_id] = {
                "type": scan_type,
                "target": target,
                "args": args,
                "status": "running",
                "progress": 0,
                "start_time": time.time(),
                "last_update": time.time(),
                "result": None,
                "error": None,
                "current_phase": "initializing",
                "message": "Scan starting..."
            }
        
        # Start scan in background
        future = self.executor.submit(self._run_scan, scan_id, scan_type, target, args)
        self.active_scans[scan_id]["future"] = future
        
        
        LOG.info(f"Started {scan_type} scan", extra={"extra": {"scan_id": scan_id, "target": target}})
        return scan_id
    
    def _run_scan(self, scan_id: str, scan_type: str, target: str, args: Dict[str, Any]):
        """Run the actual scan in background thread"""
        try:
            with self.lock:
                self.active_scans[scan_id]["status"] = "running"
            
            # Create a new session for each scan
            from config import SESSION_NAME, ZAP_BASE, APIKEY
            import requests
            import time
            
            session_name = f"{SESSION_NAME}_{int(time.time())}"
            params = {"name": session_name}
            if APIKEY:
                params["apikey"] = APIKEY
            
            try:
                url = f"{ZAP_BASE}/JSON/core/action/newSession/"
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    # Update global session ID for this scan
                    global ZAP_SESSION_ID
                    ZAP_SESSION_ID = session_name
                    LOG.info(f"Created new session for scan {scan_id}: {session_name}")
                    
                    # Clear all alerts for clean scan start
                    try:
                        clear_params = {}
                        if APIKEY:
                            clear_params["apikey"] = APIKEY
                        clear_url = f"{ZAP_BASE}/JSON/core/action/deleteAllAlerts/"
                        clear_response = requests.get(clear_url, params=clear_params, timeout=10)
                        if clear_response.status_code == 200:
                            LOG.info(f"Cleared all alerts for scan {scan_id}")
                        else:
                            LOG.warning(f"Failed to clear alerts for scan {scan_id}: HTTP {clear_response.status_code}")
                    except Exception as e:
                        LOG.warning(f"Exception clearing alerts for scan {scan_id}: {e}")
                        
                else:
                    LOG.warning(f"Failed to create new session for scan {scan_id}, using existing session")
            except Exception as e:
                LOG.warning(f"Exception creating new session for scan {scan_id}: {e}, using existing session")
            
            # Create progress callback
            def progress_callback(scan_id: str, scan_phase: str, progress: int, message: str):
                with self.lock:
                    if scan_id in self.active_scans:
                        self.active_scans[scan_id]["progress"] = progress
                        self.active_scans[scan_id]["last_update"] = time.time()
                        self.active_scans[scan_id]["current_phase"] = scan_phase
                        self.active_scans[scan_id]["message"] = message
            
            if scan_type == "active":
                result = self._run_active_scan(scan_id, target, args, progress_callback)
            elif scan_type == "complete":
                result = self._run_complete_scan(scan_id, target, args, progress_callback)
            elif scan_type == "passive":
                result = self._run_passive_scan(scan_id, target, args, progress_callback)
            elif scan_type == "ajax":
                result = self._run_ajax_scan(scan_id, target, args, progress_callback)
            else:
                raise ValueError(f"Unknown scan type: {scan_type}")
            
            with self.lock:
                self.active_scans[scan_id]["status"] = "completed"
                self.active_scans[scan_id]["result"] = result
                self.active_scans[scan_id]["progress"] = 100
                self.active_scans[scan_id]["last_update"] = time.time()
                self.active_scans[scan_id]["message"] = "Scan completed successfully"
            
            LOG.info(f"Completed {scan_type} scan", extra={"extra": {"scan_id": scan_id, "target": target}})
            
            
        except Exception as e:
            with self.lock:
                self.active_scans[scan_id]["status"] = "failed"
                self.active_scans[scan_id]["error"] = str(e)
                self.active_scans[scan_id]["last_update"] = time.time()
                self.active_scans[scan_id]["message"] = f"Scan failed: {str(e)}"
            
            LOG.error(f"Failed {scan_type} scan", extra={"extra": {"scan_id": scan_id, "error": str(e)}})
            
    
    def _run_active_scan(self, scan_id: str, target: str, args: Dict[str, Any], progress_callback: callable):
        """Run active scan synchronously"""
        target = _prepare(scan_id, target)
        
        # Spider first (optional)
        try:
            spider_timeout = min(args.get("spider_max_wait_seconds", 1800), 600)
            run_spider(scan_id, target, args.get("recurse", True), args.get("inScopeOnly", False), 
                      args.get("poll_interval_seconds", 1.5), spider_timeout, session_id=ZAP_SESSION_ID, 
                      progress_callback=progress_callback)
        except Exception as e:
            LOG.warning(f"Spider failed, continuing with active scan", extra={"extra": {"scan_id": scan_id, "error": str(e)}})
        
        # Active scan
        ascan_id, ascan_duration = run_ascan(scan_id, target, args.get("recurse", True), 
                                            args.get("inScopeOnly", False), args.get("scanPolicyName"), 
                                            args.get("poll_interval_seconds", 1.5), 
                                            args.get("ascan_max_wait_seconds", 7200), 
                                            session_id=ZAP_SESSION_ID, progress_callback=progress_callback)
        
        result = _finalize(scan_id, target, args.get("include_findings", True), 
                         args.get("include_evidence", False), 
                         {"pscan": 0.0, "ajax": 0.0, "spider": 0.0, "ascan": ascan_duration}, 
                         mode="active")
        result["activeScan"] = {"scanId": ascan_id, "duration_seconds": round(ascan_duration, 2)}
        return result
    
    def _run_complete_scan(self, scan_id: str, target: str, args: Dict[str, Any], progress_callback: callable):
        """Run complete scan synchronously"""
        target = _prepare(scan_id, target)
        
        # AJAX
        opts = AjaxOptions(
            inScope=args.get("ajax_inScope", True),
            subtreeOnly=args.get("ajax_subtreeOnly", False),
            maxCrawlDepth=args.get("ajax_maxCrawlDepth", 10),
            maxCrawlStates=args.get("ajax_maxCrawlStates", 0),
            maxDuration=args.get("ajax_maxDuration", 60),
            eventWait=args.get("ajax_eventWait", 1000),
            clickDefaultElems=args.get("ajax_clickDefaultElems", True),
            clickElemsOnce=args.get("ajax_clickElemsOnce", True),
            browserId=args.get("ajax_browserId"),
            wait_seconds=args.get("ajax_wait_seconds", 300),
            poll_interval_seconds=args.get("poll_interval_seconds", 1.5),
        )
        ok, ajax_duration, ajax_results = run_ajax(scan_id, target, opts, session_id=ZAP_SESSION_ID)
        
        # Spider
        spider_id, spider_duration = run_spider(scan_id, target, args.get("recurse", True), 
                                              args.get("inScopeOnly", False), 
                                              args.get("poll_interval_seconds", 1.5), 
                                              args.get("spider_max_wait_seconds", 1800), 
                                              session_id=ZAP_SESSION_ID, progress_callback=progress_callback)
        
        # Active
        ascan_id, ascan_duration = run_ascan(scan_id, target, args.get("recurse", True), 
                                            args.get("inScopeOnly", False), args.get("scanPolicyName"), 
                                            args.get("poll_interval_seconds", 1.5), 
                                            args.get("ascan_max_wait_seconds", 7200), 
                                            session_id=ZAP_SESSION_ID, progress_callback=progress_callback)
        
        # Passive
        pscan_duration = 0.0
        if args.get("wait_for_passive", True):
            from scans.passive import pscan_wait
            pscan_duration = pscan_wait(scan_id, args.get("passive_poll_interval_seconds", 0.5), 
                                       args.get("passive_timeout_seconds", 600), session_id=ZAP_SESSION_ID)
        
        result = _finalize(scan_id, target, args.get("include_findings", True), 
                         args.get("include_evidence", False), 
                         {"pscan": pscan_duration, "ajax": ajax_duration, "spider": spider_duration, "ascan": ascan_duration}, 
                         mode="complete")
        result.update({
            "ajaxSpider": {"started": ok, "duration_seconds": round(ajax_duration, 2), "numberOfResults": ajax_results},
            "spider": {"scanId": spider_id, "duration_seconds": round(spider_duration, 2)},
            "activeScan": {"scanId": ascan_id, "duration_seconds": round(ascan_duration, 2)},
            "passiveScan": {"waited": bool(args.get("wait_for_passive", True)), "duration_seconds": round(pscan_duration, 2)},
        })
        return result
    
    def _run_passive_scan(self, scan_id: str, target: str, args: Dict[str, Any], progress_callback: callable):
        """Run passive scan synchronously"""
        target = _prepare(scan_id, target)
        
        # Enable passive scanning
        from http_session import get_json
        try:
            get_json(scan_id, "/JSON/pscan/action/setEnabled/", {"enabled": "true"}, session_id=ZAP_SESSION_ID)
            get_json(scan_id, "/JSON/pscan/action/enableAllScanners/", {}, session_id=ZAP_SESSION_ID)
        except Exception as e:
            return {"error": f"Failed to enable passive scanning: {str(e)}"}
        
        # Wait for passive scan to complete
        timeout_seconds = args.get("timeout_seconds", 600)
        poll_interval = args.get("poll_interval_seconds", 0.5)
        
        from scans.passive import pscan_wait
        pscan_duration = pscan_wait(scan_id, poll_interval, timeout_seconds, session_id=ZAP_SESSION_ID)
        
        # Get results
        result = passive_scan_impl(scan_id, target, args.get("include_findings", True), 
                                 args.get("include_evidence", False), session_id=ZAP_SESSION_ID)
        result.update({
            "scanId": scan_id,
            "target": target,
            "duration_seconds": round(pscan_duration, 2),
            "type": "passive"
        })
        return result
    
    def _run_ajax_scan(self, scan_id: str, target: str, args: Dict[str, Any], progress_callback: callable):
        """Run AJAX scan synchronously"""
        target = _prepare(scan_id, target)
        
        # First run traditional spider to discover URLs
        try:
            spider_timeout = min(args.get("spider_max_wait_seconds", 300), 300)  # Max 5 minutes for spider
            spider_id, spider_duration = run_spider(scan_id, target, args.get("recurse", True), 
                                                  args.get("inScopeOnly", False), 
                                                  args.get("poll_interval_seconds", 1.0), 
                                                  spider_timeout, session_id=ZAP_SESSION_ID, 
                                                  progress_callback=progress_callback)
        except Exception as e:
            LOG.warning(f"Spider failed, continuing with AJAX scan", extra={"extra": {"scan_id": scan_id, "error": str(e)}})
            spider_id, spider_duration = "0", 0.0
        
        # Configure AJAX options
        opts = AjaxOptions(
            inScope=args.get("inScope", True),
            subtreeOnly=args.get("subtreeOnly", False),
            maxCrawlDepth=args.get("maxCrawlDepth", 10),
            maxCrawlStates=args.get("maxCrawlStates", 0),
            maxDuration=args.get("maxDuration", 60),
            eventWait=args.get("eventWait", 1000),
            clickDefaultElems=args.get("clickDefaultElems", True),
            clickElemsOnce=args.get("clickElemsOnce", True),
            browserId=args.get("browserId"),
            wait_seconds=args.get("wait_seconds", 300),
            poll_interval_seconds=args.get("poll_interval_seconds", 1.0)
        )
        
        # Then run AJAX spider to discover additional URLs
        ok, ajax_duration, ajax_results = run_ajax(scan_id, target, opts, session_id=ZAP_SESSION_ID)
        
        result = {
            "scanId": scan_id,
            "target": target,
            "spider": {
                "scanId": spider_id,
                "duration_seconds": round(spider_duration, 2)
            },
            "ajaxSpider": {
                "started": ok,
                "duration_seconds": round(ajax_duration, 2),
                "numberOfResults": ajax_results
            },
            "type": "ajax"
        }
        return result
    
    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """Get current status of a scan"""
        with self.lock:
            if scan_id not in self.active_scans:
                return {"error": "Scan not found"}
            
            scan_info = self.active_scans[scan_id].copy()
            # Remove future object from response
            scan_info.pop("future", None)
            
            # Add runtime information
            current_time = time.time()
            scan_info["runtime_seconds"] = round(current_time - scan_info["start_time"], 2)
            scan_info["last_update_ago_seconds"] = round(current_time - scan_info["last_update"], 2)
            
            return scan_info
    
    def cancel_scan(self, scan_id: str) -> bool:
        """Cancel a running scan"""
        with self.lock:
            if scan_id not in self.active_scans:
                return False
            
            scan_info = self.active_scans[scan_id]
            if scan_info["status"] == "running":
                # Try to cancel the future
                future = scan_info.get("future")
                if future:
                    future.cancel()
                
                scan_info["status"] = "cancelled"
                scan_info["last_update"] = time.time()
                return True
            return False
    
    def list_scans(self) -> Dict[str, Any]:
        """List all active scans"""
        with self.lock:
            scans = {}
            current_time = time.time()
            for scan_id, scan_info in self.active_scans.items():
                scans[scan_id] = {
                    "type": scan_info["type"],
                    "target": scan_info["target"],
                    "status": scan_info["status"],
                    "progress": scan_info["progress"],
                    "start_time": scan_info["start_time"],
                    "last_update": scan_info["last_update"],
                    "runtime_seconds": round(current_time - scan_info["start_time"], 2),
                    "last_update_ago_seconds": round(current_time - scan_info["last_update"], 2),
                    "current_phase": scan_info.get("current_phase", "unknown"),
                    "message": scan_info.get("message", "")
                }
            return scans
    

# Global scan manager instance
scan_manager = ScanManager()

# Heartbeat mechanism to prevent MCP server timeouts
class HeartbeatManager:
    def __init__(self):
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # 30 seconds
        self.is_running = False
        self.heartbeat_task = None
    
    async def start_heartbeat(self):
        """Start the heartbeat mechanism"""
        if self.is_running:
            return
        
        self.is_running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        LOG.info("Heartbeat mechanism started")
    
    async def stop_heartbeat(self):
        """Stop the heartbeat mechanism"""
        self.is_running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        LOG.info("Heartbeat mechanism stopped")
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to keep MCP server alive"""
        while self.is_running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                self.last_heartbeat = time.time()
                
                # Log heartbeat if there are active scans
                active_scans = scan_manager.list_scans()
                if active_scans:
                    LOG.debug(f"Heartbeat: {len(active_scans)} active scans", 
                             extra={"extra": {"active_scans": len(active_scans)}})
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                LOG.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

# Global heartbeat manager instance
heartbeat_manager = HeartbeatManager()


app = Server("zap-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="start_active_scan",
            description="Start an active security scan on a target URL (asynchronous)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri", "description": "Target URL to scan"},
                    "recurse": {"type": "boolean", "default": True, "description": "Whether to recurse into subdirectories"},
                    "inScopeOnly": {"type": "boolean", "default": False, "description": "Only scan URLs in scope"},
                    "scanPolicyName": {"type": "string", "description": "Name of the scan policy to use"},
                    "poll_interval_seconds": {"type": "number", "default": 1.5, "description": "Polling interval in seconds"},
                    "ascan_max_wait_seconds": {"type": "integer", "default": 7200, "description": "Maximum wait time for active scan (default: 2 hours)"},
                    "spider_max_wait_seconds": {"type": "integer", "default": 1800, "description": "Maximum wait time for spider (default: 30 minutes)"},
                    "include_findings": {"type": "boolean", "default": True, "description": "Include findings in results"},
                    "include_evidence": {"type": "boolean", "default": False, "description": "Include evidence in results"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="start_complete_scan",
            description="Start a complete security scan including AJAX, spider, and active scanning (asynchronous)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri", "description": "Target URL to scan"},
                    "recurse": {"type": "boolean", "default": True, "description": "Whether to recurse into subdirectories"},
                    "inScopeOnly": {"type": "boolean", "default": False, "description": "Only scan URLs in scope"},
                    "scanPolicyName": {"type": "string", "description": "Name of the scan policy to use"},
                    "poll_interval_seconds": {"type": "number", "default": 1.5, "description": "Polling interval in seconds"},
                    "ascan_max_wait_seconds": {"type": "integer", "default": 7200, "description": "Maximum wait time for active scan (default: 2 hours)"},
                    "spider_max_wait_seconds": {"type": "integer", "default": 1800, "description": "Maximum wait time for spider (default: 30 minutes)"},
                    "include_findings": {"type": "boolean", "default": True, "description": "Include findings in results"},
                    "include_evidence": {"type": "boolean", "default": False, "description": "Include evidence in results"},
                    "ajax_inScope": {"type": "boolean", "default": True, "description": "AJAX spider in scope only"},
                    "ajax_subtreeOnly": {"type": "boolean", "default": False, "description": "AJAX spider subtree only"},
                    "ajax_maxCrawlDepth": {"type": "integer", "default": 10, "description": "Maximum crawl depth for AJAX spider"},
                    "ajax_maxCrawlStates": {"type": "integer", "default": 0, "description": "Maximum crawl states for AJAX spider"},
                    "ajax_maxDuration": {"type": "integer", "default": 60, "description": "Maximum duration for AJAX spider"},
                    "ajax_eventWait": {"type": "integer", "default": 1000, "description": "Event wait time for AJAX spider"},
                    "ajax_clickDefaultElems": {"type": "boolean", "default": True, "description": "Click default elements in AJAX spider"},
                    "ajax_clickElemsOnce": {"type": "boolean", "default": True, "description": "Click elements once in AJAX spider"},
                    "ajax_browserId": {"type": "string", "description": "Browser ID for AJAX spider"},
                    "ajax_wait_seconds": {"type": "integer", "default": 300, "description": "Wait time for AJAX spider"},
                    "wait_for_passive": {"type": "boolean", "default": True, "description": "Wait for passive scan to complete"},
                    "passive_poll_interval_seconds": {"type": "number", "default": 0.5, "description": "Passive scan polling interval"},
                    "passive_timeout_seconds": {"type": "integer", "default": 600, "description": "Passive scan timeout"},
                    "disable_websocket": {"type": "boolean", "default": False, "description": "Disable websocket scanning"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="start_passive_scan",
            description="Start a passive security scan on a target URL (asynchronous)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri", "description": "Target URL to scan"},
                    "include_findings": {"type": "boolean", "default": True, "description": "Include findings in results"},
                    "include_evidence": {"type": "boolean", "default": False, "description": "Include evidence in results"},
                    "poll_interval_seconds": {"type": "number", "default": 0.5, "description": "Polling interval in seconds"},
                    "timeout_seconds": {"type": "integer", "default": 600, "description": "Maximum wait time for passive scan"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="get_scan_status",
            description="Get the status of a running scan",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_id": {"type": "string", "description": "Scan ID returned by start_*_scan"}
                },
                "required": ["scan_id"]
            }
        ),
        Tool(
            name="cancel_scan",
            description="Cancel a running scan",
            inputSchema={
                "type": "object",
                "properties": {
                    "scan_id": {"type": "string", "description": "Scan ID returned by start_*_scan"}
                },
                "required": ["scan_id"]
            }
        ),
        Tool(
            name="list_scans",
            description="List all active scans",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="start_heartbeat",
            description="Start heartbeat mechanism to prevent MCP server timeouts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="create_new_session",
            description="Manually create a new ZAP session with unique timestamp",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_name": {"type": "string", "description": "Optional custom session name (default: auto-generated with timestamp)"}
                },
                "description": "Creates a new ZAP session and returns the session ID"
            }
        ),
        Tool(
            name="start_ajax_scan",
            description="Start an AJAX spider scan on a target URL (asynchronous)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri", "description": "Target URL to scan"},
                    "recurse": {"type": "boolean", "default": True, "description": "Whether to recurse into subdirectories"},
                    "inScopeOnly": {"type": "boolean", "default": False, "description": "Only scan URLs in scope"},
                    "spider_max_wait_seconds": {"type": "integer", "default": 300, "description": "Maximum wait time for spider (default: 5 minutes)"},
                    "inScope": {"type": "boolean", "default": True, "description": "AJAX spider in scope only"},
                    "subtreeOnly": {"type": "boolean", "default": False, "description": "AJAX spider subtree only"},
                    "maxCrawlDepth": {"type": "integer", "default": 10, "description": "Maximum crawl depth for AJAX spider"},
                    "maxCrawlStates": {"type": "integer", "default": 0, "description": "Maximum crawl states for AJAX spider"},
                    "maxDuration": {"type": "integer", "default": 60, "description": "Maximum duration for AJAX spider"},
                    "eventWait": {"type": "integer", "default": 1000, "description": "Event wait time for AJAX spider"},
                    "clickDefaultElems": {"type": "boolean", "default": True, "description": "Click default elements in AJAX spider"},
                    "clickElemsOnce": {"type": "boolean", "default": True, "description": "Click elements once in AJAX spider"},
                    "browserId": {"type": "string", "description": "Browser ID for AJAX spider"},
                    "wait_seconds": {"type": "integer", "default": 300, "description": "Wait time for AJAX spider"},
                    "poll_interval_seconds": {"type": "number", "default": 1.0, "description": "Polling interval in seconds"}
                },
                "required": ["url"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    if name == "start_active_scan":
        scan_id = scan_manager.start_scan(uuid.uuid4().hex[:8], "active", arguments["url"], arguments)
        result = {"scan_id": scan_id, "status": "started", "message": "Active scan started in background"}
        return [TextContent(type="text", text=str(result))]
    elif name == "start_complete_scan":
        scan_id = scan_manager.start_scan(uuid.uuid4().hex[:8], "complete", arguments["url"], arguments)
        result = {"scan_id": scan_id, "status": "started", "message": "Complete scan started in background"}
        return [TextContent(type="text", text=str(result))]
    elif name == "start_ajax_scan":
        scan_id = scan_manager.start_scan(uuid.uuid4().hex[:8], "ajax", arguments["url"], arguments)
        result = {"scan_id": scan_id, "status": "started", "message": "AJAX scan started in background"}
        return [TextContent(type="text", text=str(result))]
    elif name == "start_passive_scan":
        scan_id = scan_manager.start_scan(uuid.uuid4().hex[:8], "passive", arguments["url"], arguments)
        result = {"scan_id": scan_id, "status": "started", "message": "Passive scan started in background"}
        return [TextContent(type="text", text=str(result))]
    elif name == "get_scan_status":
        result = scan_manager.get_scan_status(arguments["scan_id"])
        return [TextContent(type="text", text=str(result))]
    elif name == "cancel_scan":
        success = scan_manager.cancel_scan(arguments["scan_id"])
        result = {"success": success, "message": "Scan cancelled" if success else "Scan not found or not running"}
        return [TextContent(type="text", text=str(result))]
    elif name == "list_scans":
        result = scan_manager.list_scans()
        return [TextContent(type="text", text=str(result))]
    elif name == "start_heartbeat":
        await heartbeat_manager.start_heartbeat()
        result = {"success": True, "message": "Heartbeat mechanism started"}
        return [TextContent(type="text", text=str(result))]
    elif name == "create_new_session":
        from config import SESSION_NAME, ZAP_BASE, APIKEY
        from zap_control import ZAP_SESSION_ID
        import requests
        import time
        import urllib.parse
        
        # Generate session name
        custom_name = arguments.get("session_name")
        if custom_name:
            session_name = custom_name
        else:
            session_name = f"{SESSION_NAME}_{int(time.time())}"
        
        # Create new session via ZAP API
        params = {"name": session_name}
        if APIKEY:
            params["apikey"] = APIKEY
        
        try:
            url = f"{ZAP_BASE}/JSON/core/action/newSession/"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Update global session ID
                global ZAP_SESSION_ID
                ZAP_SESSION_ID = session_name
                
                result = {
                    "success": True,
                    "session_id": session_name,
                    "message": f"New session '{session_name}' created successfully",
                    "timestamp": int(time.time()),
                    "zap_response": response.json() if response.text else "OK"
                }
            else:
                result = {
                    "success": False,
                    "error": f"Failed to create session. HTTP {response.status_code}",
                    "response": response.text,
                    "session_name": session_name
                }
        except Exception as e:
            result = {
                "success": False,
                "error": f"Exception creating session: {str(e)}",
                "session_name": session_name
            }
        
        return [TextContent(type="text", text=str(result))]
    else:
        raise ValueError(f"Unknown tool: {name}")


