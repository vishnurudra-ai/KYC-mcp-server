"""Tests for System Diagnostics MCP Server"""

import pytest
import json
import platform
from unittest.mock import Mock, patch
from system_diagnostics_mcp.server import SystemDiagnosticsServer, SystemInfo


@pytest.fixture
async def server():
    """Create a server instance for testing"""
    return SystemDiagnosticsServer()


@pytest.mark.asyncio
async def test_server_initialization(server):
    """Test server initializes correctly"""
    assert server is not None
    assert server.os_type == platform.system()
    assert server.server is not None


@pytest.mark.asyncio
async def test_get_system_info(server):
    """Test getting system information"""
    result = await server.get_system_info({})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "system_info" in data
    assert "os_type" in data["system_info"]
    assert "hostname" in data["system_info"]
    assert "total_ram_gb" in data["system_info"]
    assert data["system_info"]["total_ram_gb"] > 0


@pytest.mark.asyncio
async def test_get_cpu_metrics(server):
    """Test getting CPU metrics"""
    result = await server.get_cpu_metrics({"interval": 0.1})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "usage_percent" in data
    assert isinstance(data["usage_percent"], (int, float))
    assert 0 <= data["usage_percent"] <= 100


@pytest.mark.asyncio
async def test_get_memory_metrics(server):
    """Test getting memory metrics"""
    result = await server.get_memory_metrics({"include_processes": False})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "virtual_memory" in data
    assert "swap_memory" in data
    assert "percent" in data["virtual_memory"]
    assert 0 <= data["virtual_memory"]["percent"] <= 100


@pytest.mark.asyncio
async def test_get_storage_metrics(server):
    """Test getting storage metrics"""
    result = await server.get_storage_metrics({"include_io_stats": False})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "partitions" in data
    assert len(data["partitions"]) > 0
    
    for partition in data["partitions"]:
        assert "device" in partition
        assert "total_gb" in partition
        assert "percent" in partition


@pytest.mark.asyncio
async def test_get_processes(server):
    """Test getting process information"""
    result = await server.get_processes({"sort_by": "cpu", "limit": 5})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "processes" in data
    assert "total" in data
    assert len(data["processes"]) <= 5
    
    if len(data["processes"]) > 0:
        proc = data["processes"][0]
        assert "pid" in proc
        assert "name" in proc
        assert "cpu_percent" in proc


@pytest.mark.asyncio
async def test_diagnose_performance(server):
    """Test performance diagnostics"""
    result = await server.diagnose_performance({"duration": 1})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "metrics" in data
    assert "bottlenecks" in data
    assert "recommendations" in data
    assert "cpu" in data["metrics"]
    assert "memory" in data["metrics"]


@pytest.mark.asyncio
async def test_get_hardware_recommendations(server):
    """Test hardware recommendations"""
    result = await server.get_hardware_recommendations({"use_case": "general"})
    assert len(result) == 1
    
    data = json.loads(result[0].text)
    assert "current_specs" in data
    assert "upgrade_recommendations" in data
    assert "compatibility_notes" in data


@pytest.mark.asyncio
async def test_error_handling(server):
    """Test error handling in server methods"""
    # Test with invalid arguments
    with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
        result = await server.get_cpu_metrics({})
        assert len(result) == 1
        assert "Error:" in result[0].text