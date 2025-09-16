#!/usr/bin/env python3
"""
Simple script to run the ZAP MCP server with proper path configuration.
This fixes the import issues when running the module.
"""

import sys
from pathlib import Path

# Add the current directory to the path to fix imports
sys.path.append(str(Path(__file__).parent))

# Import and run the server
from zap_custom_mcp.http_server import main

if __name__ == "__main__":
    main()
