# MCP Server implementation
import functools
import sys
from pathlib import Path
from typing import Any, Callable

# Add the parent directory to the path to fix imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mcp.types import TextContent, Tool
from mcp.server.models import InitializationOptions


class Server:
    """MCP Server implementation"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.tools: list = []
        self.initialized = False
        self._list_tools_func = None
        self._call_tool_func = None

    def add_tool(self, tool: Tool):
        """Add a tool to the server"""
        self.tools.append(tool)

    def get_tools(self) -> list:
        """Get all available tools"""
        return self.tools

    def call_tool_by_name(self, name: str, arguments: dict) -> any:
        """Call a tool by name with arguments"""
        for tool in self.tools:
            if tool.name == name:
                # This would be implemented by the actual tool handlers
                return {"result": f"Tool {name} called with {arguments}"}
        raise ValueError(f"Tool {name} not found")

    def list_tools(self) -> Callable:
        """Decorator for list_tools function"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self._list_tools_func = wrapper
            return wrapper

        return decorator

    def call_tool(self) -> Callable:
        """Decorator for call_tool function"""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self._call_tool_func = wrapper
            return wrapper

        return decorator


__all__ = ["Server", "Tool", "TextContent", "InitializationOptions"]
