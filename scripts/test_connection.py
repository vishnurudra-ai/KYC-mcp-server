#!/usr/bin/env python3
"""Test script to verify MCP server connection"""

import asyncio
import json
import sys
from system_diagnostics_mcp.server import SystemDiagnosticsServer


async def test_server():
    """Test basic server functionality"""
    print("Testing System Diagnostics MCP Server...")
    print("-" * 40)
    
    try:
        server = SystemDiagnosticsServer()
        print("✓ Server initialized successfully")
        
        # Test system info
        print("\nTesting get_system_info...")
        result = await server.get_system_info({})
        data = json.loads(result[0].text)
        print(f"✓ OS Type: {data['system_info']['os_type']}")
        print(f"✓ Hostname: {data['system_info']['hostname']}")
        print(f"✓ CPU Cores: {data['system_info']['logical_cores']}")
        print(f"✓ RAM: {data['system_info']['total_ram_gb']} GB")
        
        # Test CPU metrics
        print("\nTesting get_cpu_metrics...")
        result = await server.get_cpu_metrics({"interval": 1})
        data = json.loads(result[0].text)
        print(f"✓ CPU Usage: {data['usage_percent']}%")
        
        # Test memory metrics
        print("\nTesting get_memory_metrics...")
        result = await server.get_memory_metrics({})
        data = json.loads(result[0].text)
        print(f"✓ Memory Usage: {data['virtual_memory']['percent']}%")
        
        print("\n" + "=" * 40)
        print("All tests passed successfully!")
        print("The server is ready to use with Claude Desktop.")
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_server())
    sys.exit(exit_code)