#!/usr/bin/env python3
"""
Entry point for running zap_custom_mcp as a module.
This allows both: python -m zap_custom_mcp and python -m zap_custom_mcp.http_server
"""

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add the current directory to the path to fix imports
    sys.path.append(str(Path(__file__).parent))
    
    from http_server import main

    main()
