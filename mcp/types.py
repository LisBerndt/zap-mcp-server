# MCP Types
from typing import Dict, Any

class Tool:
    """MCP Tool definition"""
    def __init__(self, name: str, description: str, inputSchema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema

class TextContent:
    """MCP Text Content"""
    def __init__(self, text: str, type: str = "text"):
        self.text = text
        self.type = type
