#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加search_mcp路径
search_mcp_path = Path(__file__).parent / "search_mcp" / "src"
sys.path.insert(0, str(search_mcp_path))

print(f"Testing search_mcp import...")
print(f"Search MCP path: {search_mcp_path}")
print(f"Path exists: {search_mcp_path.exists()}")
print(f"Config file exists: {(search_mcp_path / 'search_mcp' / 'config.py').exists()}")

try:
    print("\nAttempting to import search_mcp.config...")
    from search_mcp.config import SearchConfig
    print("✅ Import successful!")
    
    print("\nCreating SearchConfig instance...")
    config = SearchConfig()
    print("✅ Config created successfully!")
    
    print(f"\nAPI keys status: {config.get_api_keys()}")
    print(f"Enabled sources: {config.get_enabled_sources()}")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()