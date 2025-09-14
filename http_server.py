import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from server import list_tools, call_tool
from logging_setup import setup_logger
from zap_control import ensure_zap_running, ensure_session
from config import MCP_HOST, MCP_PORT, MCP_PATH, LONG_SCAN_TIMEOUT

LOG = setup_logger("zap_mcp.http_server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_zap_session()
    LOG.info(f"MCP HTTP Server started on {MCP_HOST}:{MCP_PORT}{MCP_PATH}")
    yield
    # Shutdown
    LOG.info("MCP HTTP Server shutting down")

# Create FastAPI app with extended timeout configuration
app = FastAPI(
    title="ZAP MCP Server", 
    version="1.0.0", 
    lifespan=lifespan,
    # Disable automatic timeout handling to prevent 5-minute timeouts
    docs_url=None,  # Disable docs to reduce overhead
    redoc_url=None  # Disable redoc to reduce overhead
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add timeout middleware to prevent 5-minute timeouts
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
        # Set very long timeout for MCP requests
        import asyncio
        try:
            response = await asyncio.wait_for(call_next(request), timeout=14400)  # 4 hours
            return response
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"error": "Request timeout after 4 hours"}
            )

# MCP Protocol Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Dict[str, Any] = {}
    error: Dict[str, Any] = {}

class MCPError(BaseModel):
    code: int
    message: str
    data: Dict[str, Any] = {}

def init_zap_session():
    ensure_zap_running()
    # Don't create session on startup - only when scans are started
    LOG.info("ZAP session initialized")

@app.get(MCP_PATH)
async def mcp_info():
    return {
        "message": "ZAP MCP Server",
        "version": "1.0.0",
        "protocol": "MCP over HTTP",
        "methods": ["initialize", "tools/list", "tools/call"],
        "tools": ["active_scan", "complete_scan"]
    }

@app.post(MCP_PATH)
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
        LOG.info(f"MCP Request: {body.get('method', 'unknown')} (ID: {body.get('id', 'unknown')})")
        
        method = body.get("method")
        request_id = body.get("id", "unknown")
        params = body.get("params", {})
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "zap-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            tools = await list_tools()
            tools_data = []
            for tool in tools:
                tools_data.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_data}
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            LOG.info(f"MCP tool call", extra={"extra": {"tool_name": tool_name, "request_id": request_id, "arguments": arguments}})
            
            if not tool_name:
                LOG.error(f"Tool name missing", extra={"extra": {"request_id": request_id}})
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Tool name is required"
                    }
                }
            else:
                try:
                    LOG.info(f"Executing tool", extra={"extra": {"tool_name": tool_name, "request_id": request_id, "is_long_running": tool_name in ["active_scan", "complete_scan"]}})
                    
                    # For long-running scans, use extended timeout
                    if tool_name in ["active_scan", "complete_scan"]:
                        import asyncio
                        LOG.info(f"Using extended timeout for long-running tool", extra={"extra": {"tool_name": tool_name, "timeout": LONG_SCAN_TIMEOUT}})
                        result = await asyncio.wait_for(
                            call_tool(tool_name, arguments), 
                            timeout=LONG_SCAN_TIMEOUT
                        )
                    else:
                        result = await call_tool(tool_name, arguments)
                    
                    LOG.info(f"Tool execution successful", extra={"extra": {"tool_name": tool_name, "request_id": request_id}})
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result[0].text) if result else "No result"
                                }
                            ]
                        }
                    }
                except asyncio.TimeoutError:
                    LOG.error(f"Tool execution timeout", extra={"extra": {"tool_name": tool_name, "request_id": request_id, "timeout": LONG_SCAN_TIMEOUT}})
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution timed out after {LONG_SCAN_TIMEOUT} seconds"
                        }
                    }
                except Exception as e:
                    LOG.error(f"Tool execution failed", extra={"extra": {"tool_name": tool_name, "request_id": request_id, "error": str(e)}})
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {str(e)}"
                        }
                    }
            
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
        return response
        
    except Exception as e:
        LOG.error(f"MCP Error: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id", "unknown") if 'body' in locals() else "unknown",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.post(MCP_PATH + "/raw")
async def mcp_endpoint_raw(request: Request):
    try:
        body = await request.json()
        LOG.info(f"MCP Raw Request: {body.get('method', 'unknown')} (ID: {body.get('id', 'unknown')})")
        
        method = body.get("method")
        request_id = body.get("id", "unknown")
        params = body.get("params", {})
        
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "zap-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            tools = await list_tools()
            tools_data = []
            for tool in tools:
                tools_data.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_data}
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Tool name is required"
                    }
                }
            else:
                try:
                    # For long-running scans, use extended timeout
                    if tool_name in ["active_scan", "complete_scan"]:
                        import asyncio
                        result = await asyncio.wait_for(
                            call_tool(tool_name, arguments), 
                            timeout=LONG_SCAN_TIMEOUT
                        )
                    else:
                        result = await call_tool(tool_name, arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result[0].text) if result else "No result"
                                }
                            ]
                        }
                    }
                except asyncio.TimeoutError:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution timed out after {LONG_SCAN_TIMEOUT} seconds"
                        }
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution failed: {str(e)}"
                        }
                    }
                
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
        return response
        
    except Exception as e:
        LOG.error(f"MCP Raw Error: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id", "unknown") if 'body' in locals() else "unknown",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": "zap-mcp"}

@app.get("/")
async def root():
    return {
        "message": "ZAP MCP Server",
        "version": "1.0.0",
        "endpoint": MCP_PATH,
        "tools": ["active_scan", "complete_scan"]
    }

if __name__ == "__main__":
    import uvicorn
    # CRITICAL: Set longer timeout to prevent 5-minute timeout issues
    uvicorn.run(
        app, 
        host=MCP_HOST, 
        port=MCP_PORT,
        timeout_keep_alive=3600,  # 1 hour keep-alive timeout
        timeout_graceful_shutdown=300,  # 5 minutes graceful shutdown
        limit_max_requests=1000,  # Prevent connection limits
        limit_concurrency=100,  # Allow more concurrent requests
        log_level="debug",  # Enable debug logging
        access_log=True,  # Enable access logs
        use_colors=True,  # Enable colored logs
        reload=False,  # Disable reload for production
        workers=1  # Single worker for debugging
    )
