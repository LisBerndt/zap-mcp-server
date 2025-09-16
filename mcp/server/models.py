# MCP Server models
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class InitializationOptions:
    """MCP Initialization Options"""
    capabilities: Dict[str, Any]
    client_info: Optional[Dict[str, Any]] = None
