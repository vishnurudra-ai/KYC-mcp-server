#!/usr/bin/env python3
"""
System Diagnostics MCP Server
A comprehensive system monitoring and diagnostics server for the Model Context Protocol.
Provides detailed system metrics, application monitoring, and AI-powered recommendations.
"""

import json
import platform
import asyncio
import logging
import sys
import os
import subprocess
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# Core MCP imports
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# System monitoring libraries
import psutil  # Cross-platform system monitoring

# Platform-specific imports
if platform.system() == "Windows":
    import wmi
    import winreg
elif platform.system() == "Darwin":  # macOS
    import plistlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("system_diagnostics_mcp")


@dataclass
class SystemInfo:
    """System information data class"""
    os_type: str
    os_version: str
    hostname: str
    architecture: str
    processor: str
    physical_cores: int
    logical_cores: int
    total_ram_gb: float
    boot_time: float


class SystemDiagnosticsServer:
    """Main MCP server for system diagnostics"""
    
    def __init__(self):
        self.server = Server("system-diagnostics")
        self.os_type = platform.system()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up the MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="get_system_info",
                    description="Get comprehensive system information including OS, hardware, and boot time",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_cpu_metrics",
                    description="Get detailed CPU metrics including usage, frequency, temperature (if available)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "per_core": {
                                "type": "boolean",
                                "description": "Return per-core statistics",
                                "default": False
                            },
                            "interval": {
                                "type": "number",
                                "description": "Sampling interval in seconds",
                                "default": 1
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_memory_metrics",
                    description="Get detailed memory usage including RAM, swap, and per-process memory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_processes": {
                                "type": "boolean",
                                "description": "Include top memory-consuming processes",
                                "default": False
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_storage_metrics",
                    description="Get storage information for all drives including SSDs, HDDs, and usage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_io_stats": {
                                "type": "boolean",
                                "description": "Include I/O statistics",
                                "default": False
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_network_metrics",
                    description="Get network interface information and statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_connections": {
                                "type": "boolean",
                                "description": "Include active network connections",
                                "default": False
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_processes",
                    description="Get information about running processes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sort_by": {
                                "type": "string",
                                "enum": ["cpu", "memory", "name", "pid"],
                                "description": "Sort processes by this metric",
                                "default": "cpu"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of processes to return",
                                "default": 20
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_installed_applications",
                    description="Get list of installed applications on the system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by application category",
                                "default": "all"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_battery_status",
                    description="Get battery status and power consumption information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_system_logs",
                    description="Get recent system logs and events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "log_type": {
                                "type": "string",
                                "enum": ["system", "application", "security", "all"],
                                "description": "Type of logs to retrieve",
                                "default": "system"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of log entries",
                                "default": 100
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="diagnose_performance",
                    description="Run performance diagnostics and identify bottlenecks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "duration": {
                                "type": "integer",
                                "description": "Duration to monitor in seconds",
                                "default": 5
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_hardware_recommendations",
                    description="Get hardware upgrade recommendations based on system analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "use_case": {
                                "type": "string",
                                "enum": ["gaming", "productivity", "development", "content_creation", "general"],
                                "description": "Primary use case for recommendations",
                                "default": "general"
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_motherboard_details",
                    description="Get detailed motherboard information including manufacturer, model, BIOS, and hardware specifications",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_bios": {
                                "type": "boolean",
                                "description": "Include BIOS/UEFI information",
                                "default": True
                            },
                            "include_slots": {
                                "type": "boolean",
                                "description": "Include expansion slot information",
                                "default": True
                            }
                        },
                        "required": []
                    }
                ),
                types.Tool(
                    name="get_computer_model",
                    description="Get computer model and manufacturer information from the system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include additional system details like SKU, UUID, and system family",
                                "default": True
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            if name == "get_system_info":
                return await self.get_system_info(arguments)
            elif name == "get_cpu_metrics":
                return await self.get_cpu_metrics(arguments)
            elif name == "get_memory_metrics":
                return await self.get_memory_metrics(arguments)
            elif name == "get_storage_metrics":
                return await self.get_storage_metrics(arguments)
            elif name == "get_network_metrics":
                return await self.get_network_metrics(arguments)
            elif name == "get_processes":
                return await self.get_processes(arguments)
            elif name == "get_installed_applications":
                return await self.get_installed_applications(arguments)
            elif name == "get_battery_status":
                return await self.get_battery_status(arguments)
            elif name == "get_system_logs":
                return await self.get_system_logs(arguments)
            elif name == "diagnose_performance":
                return await self.diagnose_performance(arguments)
            elif name == "get_hardware_recommendations":
                return await self.get_hardware_recommendations(arguments)
            elif name == "get_motherboard_details":
                return await self.get_motherboard_details(arguments)
            elif name == "get_computer_model":
                return await self.get_computer_model(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="system-diagnostics",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    
    async def get_system_info(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get comprehensive system information"""
        try:
            info = SystemInfo(
                os_type=platform.system(),
                os_version=platform.version(),
                hostname=platform.node(),
                architecture=platform.machine(),
                processor=platform.processor(),
                physical_cores=psutil.cpu_count(logical=False) or 0,
                logical_cores=psutil.cpu_count(logical=True) or 0,
                total_ram_gb=round(psutil.virtual_memory().total / (1024**3), 2),
                boot_time=psutil.boot_time()
            )
            
            boot_time_str = datetime.fromtimestamp(info.boot_time).strftime('%Y-%m-%d %H:%M:%S')
            uptime_seconds = time.time() - info.boot_time
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            
            result = {
                "system_info": asdict(info),
                "boot_time_formatted": boot_time_str,
                "uptime": f"{uptime_days} days, {uptime_hours} hours"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_cpu_metrics(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get detailed CPU metrics"""
        try:
            per_core = arguments.get("per_core", False)
            interval = arguments.get("interval", 1)
            
            metrics = {
                "usage_percent": psutil.cpu_percent(interval=interval, percpu=per_core),
                "frequency": {}
            }
            
            # CPU frequency
            freq = psutil.cpu_freq(percpu=per_core)
            if freq:
                if per_core:
                    metrics["frequency"] = [
                        {"current": f.current, "min": f.min, "max": f.max} 
                        for f in freq
                    ]
                else:
                    metrics["frequency"] = {
                        "current": freq.current,
                        "min": freq.min,
                        "max": freq.max
                    }
            
            # CPU stats
            stats = psutil.cpu_stats()
            metrics["stats"] = {
                "ctx_switches": stats.ctx_switches,
                "interrupts": stats.interrupts,
                "soft_interrupts": stats.soft_interrupts,
                "syscalls": stats.syscalls
            }
            
            # CPU times
            times = psutil.cpu_times()
            metrics["times"] = {
                "user": times.user,
                "system": times.system,
                "idle": times.idle
            }
            
            # Temperature (if available)
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    metrics["temperatures"] = {}
                    for name, entries in temps.items():
                        metrics["temperatures"][name] = [
                            {"label": e.label, "current": e.current, "high": e.high, "critical": e.critical}
                            for e in entries
                        ]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting CPU metrics: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_memory_metrics(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get detailed memory metrics"""
        try:
            include_processes = arguments.get("include_processes", False)
            
            # Virtual memory
            vm = psutil.virtual_memory()
            metrics = {
                "virtual_memory": {
                    "total_gb": round(vm.total / (1024**3), 2),
                    "available_gb": round(vm.available / (1024**3), 2),
                    "used_gb": round(vm.used / (1024**3), 2),
                    "free_gb": round(vm.free / (1024**3), 2),
                    "percent": vm.percent
                }
            }
            
            # Swap memory
            swap = psutil.swap_memory()
            metrics["swap_memory"] = {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "free_gb": round(swap.free / (1024**3), 2),
                "percent": swap.percent
            }
            
            # Top memory-consuming processes
            if include_processes:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
                    try:
                        pinfo = proc.info
                        processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "memory_percent": round(pinfo['memory_percent'], 2),
                            "memory_mb": round(pinfo['memory_info'].rss / (1024**2), 2)
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
                metrics["top_processes"] = processes[:10]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting memory metrics: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_storage_metrics(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get storage metrics for all drives"""
        try:
            include_io = arguments.get("include_io_stats", False)
            
            metrics = {"partitions": []}
            
            # Disk partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    }
                    
                    # Try to determine if SSD or HDD (platform-specific)
                    if self.os_type == "Windows":
                        partition_info["type"] = self._get_windows_drive_type(partition.device)
                    elif self.os_type == "Darwin":
                        partition_info["type"] = self._get_macos_drive_type(partition.device)
                    else:
                        partition_info["type"] = "Unknown"
                    
                    metrics["partitions"].append(partition_info)
                except PermissionError:
                    continue
            
            # I/O statistics
            if include_io:
                io_counters = psutil.disk_io_counters(perdisk=True)
                metrics["io_stats"] = {}
                for disk, counters in io_counters.items():
                    metrics["io_stats"][disk] = {
                        "read_count": counters.read_count,
                        "write_count": counters.write_count,
                        "read_mb": round(counters.read_bytes / (1024**2), 2),
                        "write_mb": round(counters.write_bytes / (1024**2), 2),
                        "read_time_ms": counters.read_time,
                        "write_time_ms": counters.write_time
                    }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting storage metrics: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _get_windows_drive_type(self, device: str) -> str:
        """Determine if Windows drive is SSD or HDD"""
        try:
            if platform.system() == "Windows":
                c = wmi.WMI()
                device_id = device.replace("\\", "").replace(":", "")
                for disk in c.Win32_DiskDrive():
                    if device_id in disk.DeviceID:
                        if disk.MediaType and "SSD" in disk.MediaType:
                            return "SSD"
                        elif disk.MediaType:
                            return "HDD"
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_macos_drive_type(self, device: str) -> str:
        """Determine if macOS drive is SSD or HDD"""
        try:
            result = subprocess.run(
                ["diskutil", "info", device],
                capture_output=True,
                text=True
            )
            if "Solid State" in result.stdout:
                return "SSD"
            elif "Rotational" in result.stdout:
                return "HDD"
            return "Unknown"
        except:
            return "Unknown"
    
    async def get_network_metrics(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get network metrics"""
        try:
            include_connections = arguments.get("include_connections", False)
            
            metrics = {"interfaces": {}}
            
            # Network interfaces
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            for iface, addrs in interfaces.items():
                interface_info = {
                    "addresses": [],
                    "is_up": stats[iface].isup if iface in stats else False,
                    "speed_mbps": stats[iface].speed if iface in stats else 0
                }
                
                for addr in addrs:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    }
                    interface_info["addresses"].append(addr_info)
                
                if iface in io_counters:
                    counter = io_counters[iface]
                    interface_info["statistics"] = {
                        "bytes_sent_mb": round(counter.bytes_sent / (1024**2), 2),
                        "bytes_recv_mb": round(counter.bytes_recv / (1024**2), 2),
                        "packets_sent": counter.packets_sent,
                        "packets_recv": counter.packets_recv,
                        "errors_in": counter.errin,
                        "errors_out": counter.errout
                    }
                
                metrics["interfaces"][iface] = interface_info
            
            # Active connections
            if include_connections:
                connections = []
                for conn in psutil.net_connections(kind='inet'):
                    conn_info = {
                        "family": str(conn.family),
                        "type": str(conn.type),
                        "local_address": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        "remote_address": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status,
                        "pid": conn.pid
                    }
                    connections.append(conn_info)
                metrics["connections"] = connections[:50]  # Limit to 50 connections
            
            return [types.TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_processes(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get running processes information"""
        try:
            sort_by = arguments.get("sort_by", "cpu")
            limit = arguments.get("limit", 20)
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'status', 'create_time', 'num_threads']):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": round(pinfo['cpu_percent'], 2),
                        "memory_percent": round(pinfo['memory_percent'], 2),
                        "status": pinfo['status'],
                        "threads": pinfo['num_threads'],
                        "created": datetime.fromtimestamp(pinfo['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'])
            elif sort_by == "pid":
                processes.sort(key=lambda x: x['pid'])
            
            return [types.TextContent(
                type="text",
                text=json.dumps({"processes": processes[:limit], "total": len(processes)}, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_installed_applications(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get installed applications"""
        try:
            applications = []
            
            if self.os_type == "Windows":
                applications = self._get_windows_applications()
            elif self.os_type == "Darwin":
                applications = self._get_macos_applications()
            else:  # Linux
                applications = self._get_linux_applications()
            
            return [types.TextContent(
                type="text",
                text=json.dumps({"applications": applications, "total": len(applications)}, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting installed applications: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _get_windows_applications(self) -> List[Dict[str, Any]]:
        """Get Windows installed applications"""
        applications = []
        try:
            import winreg
            
            # Check both 32-bit and 64-bit registry keys
            keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for key_path in keys:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            app_info = {}
                            try:
                                app_info["name"] = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                app_info["version"] = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            except:
                                continue
                            
                            try:
                                app_info["publisher"] = winreg.QueryValueEx(subkey, "Publisher")[0]
                            except:
                                app_info["publisher"] = "Unknown"
                            
                            try:
                                app_info["install_date"] = winreg.QueryValueEx(subkey, "InstallDate")[0]
                            except:
                                app_info["install_date"] = "Unknown"
                            
                            applications.append(app_info)
                            winreg.CloseKey(subkey)
                        except:
                            continue
                    winreg.CloseKey(key)
                except:
                    continue
        except ImportError:
            pass
        
        return applications
    
    def _get_macos_applications(self) -> List[Dict[str, Any]]:
        """Get macOS installed applications"""
        applications = []
        try:
            apps_dir = "/Applications"
            for app in os.listdir(apps_dir):
                if app.endswith(".app"):
                    app_path = os.path.join(apps_dir, app)
                    info_plist = os.path.join(app_path, "Contents", "Info.plist")
                    
                    if os.path.exists(info_plist):
                        try:
                            with open(info_plist, 'rb') as f:
                                plist = plistlib.load(f)
                                app_info = {
                                    "name": plist.get("CFBundleName", app[:-4]),
                                    "version": plist.get("CFBundleShortVersionString", "Unknown"),
                                    "identifier": plist.get("CFBundleIdentifier", "Unknown")
                                }
                                applications.append(app_info)
                        except:
                            applications.append({"name": app[:-4], "version": "Unknown"})
        except:
            pass
        
        return applications
    
    def _get_linux_applications(self) -> List[Dict[str, Any]]:
        """Get Linux installed applications"""
        applications = []
        try:
            # Try dpkg for Debian-based systems
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n')[5:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 3:
                        applications.append({
                            "name": parts[1],
                            "version": parts[2],
                            "description": " ".join(parts[3:]) if len(parts) > 3 else ""
                        })
        except:
            # Try rpm for Red Hat-based systems
            try:
                result = subprocess.run(
                    ["rpm", "-qa"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line:
                            applications.append({"name": line, "version": "Unknown"})
            except:
                pass
        
        return applications
    
    async def get_battery_status(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get battery status and power information"""
        try:
            battery = psutil.sensors_battery()
            
            if battery is None:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"status": "No battery detected (desktop system)"}, indent=2)
                )]
            
            status = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "status": "Charging" if battery.power_plugged else "Discharging"
            }
            
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                status["time_remaining"] = f"{hours}h {minutes}m"
            else:
                status["time_remaining"] = "Calculating..." if not battery.power_plugged else "Plugged in"
            
            # Get power-hungry processes
            power_hungry = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] > 5:  # Processes using more than 5% CPU
                        power_hungry.append({
                            "name": proc.info['name'],
                            "pid": proc.info['pid'],
                            "cpu_percent": proc.info['cpu_percent']
                        })
                except:
                    pass
            
            power_hungry.sort(key=lambda x: x['cpu_percent'], reverse=True)
            status["power_hungry_processes"] = power_hungry[:5]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(status, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting battery status: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_system_logs(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get system logs"""
        try:
            log_type = arguments.get("log_type", "system")
            limit = arguments.get("limit", 100)
            
            logs = []
            
            if self.os_type == "Windows":
                logs = self._get_windows_logs(log_type, limit)
            elif self.os_type == "Darwin":
                logs = self._get_macos_logs(log_type, limit)
            else:
                logs = self._get_linux_logs(log_type, limit)
            
            return [types.TextContent(
                type="text",
                text=json.dumps({"logs": logs, "count": len(logs)}, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting system logs: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _get_windows_logs(self, log_type: str, limit: int) -> List[Dict[str, Any]]:
        """Get Windows event logs"""
        logs = []
        try:
            import win32evtlog
            
            server = 'localhost'
            logtype = 'System' if log_type == 'system' else 'Application'
            hand = win32evtlog.OpenEventLog(server, logtype)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            for event in events[:limit]:
                logs.append({
                    "time": str(event.TimeGenerated),
                    "source": event.SourceName,
                    "event_id": event.EventID,
                    "category": event.EventCategory,
                    "type": event.EventType,
                    "message": str(event.StringInserts) if event.StringInserts else ""
                })
            
            win32evtlog.CloseEventLog(hand)
        except ImportError:
            # Fallback to PowerShell if win32evtlog is not available
            try:
                result = subprocess.run(
                    ["powershell", f"Get-EventLog -LogName {log_type} -Newest {limit} | ConvertTo-Json"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    import json
                    events = json.loads(result.stdout)
                    for event in events:
                        logs.append({
                            "time": event.get("TimeGenerated", ""),
                            "source": event.get("Source", ""),
                            "message": event.get("Message", "")
                        })
            except:
                pass
        
        return logs
    
    def _get_macos_logs(self, log_type: str, limit: int) -> List[Dict[str, Any]]:
        """Get macOS system logs"""
        logs = []
        try:
            # Use log show command
            result = subprocess.run(
                ["log", "show", "--last", f"{limit}m", "--predicate", f'eventMessage contains "{log_type}"'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n')[:limit]:
                    if line:
                        parts = line.split(maxsplit=3)
                        if len(parts) >= 4:
                            logs.append({
                                "time": f"{parts[0]} {parts[1]}",
                                "type": parts[2],
                                "message": parts[3]
                            })
        except:
            pass
        
        return logs
    
    def _get_linux_logs(self, log_type: str, limit: int) -> List[Dict[str, Any]]:
        """Get Linux system logs"""
        logs = []
        try:
            # Try journalctl first
            result = subprocess.run(
                ["journalctl", "-n", str(limit), "--no-pager", "-o", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        try:
                            entry = json.loads(line)
                            logs.append({
                                "time": datetime.fromtimestamp(int(entry.get("__REALTIME_TIMESTAMP", 0)) / 1000000).isoformat(),
                                "priority": entry.get("PRIORITY", ""),
                                "unit": entry.get("_SYSTEMD_UNIT", ""),
                                "message": entry.get("MESSAGE", "")
                            })
                        except:
                            pass
            else:
                # Fallback to /var/log files
                log_file = "/var/log/syslog" if os.path.exists("/var/log/syslog") else "/var/log/messages"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-limit:]
                        for line in lines:
                            logs.append({"message": line.strip()})
        except:
            pass
        
        return logs
    
    async def diagnose_performance(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Run performance diagnostics"""
        try:
            duration = arguments.get("duration", 5)
            
            # Initial snapshot
            cpu_before = psutil.cpu_percent(interval=1)
            mem_before = psutil.virtual_memory().percent
            disk_io_before = psutil.disk_io_counters()
            net_io_before = psutil.net_io_counters()
            
            # Monitor for specified duration
            cpu_samples = []
            mem_samples = []
            for _ in range(duration):
                cpu_samples.append(psutil.cpu_percent(interval=1))
                mem_samples.append(psutil.virtual_memory().percent)
            
            # Final snapshot
            disk_io_after = psutil.disk_io_counters()
            net_io_after = psutil.net_io_counters()
            
            # Analysis
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            avg_mem = sum(mem_samples) / len(mem_samples)
            max_mem = max(mem_samples)
            
            # Calculate I/O rates
            disk_read_rate = (disk_io_after.read_bytes - disk_io_before.read_bytes) / duration / (1024**2)  # MB/s
            disk_write_rate = (disk_io_after.write_bytes - disk_io_before.write_bytes) / duration / (1024**2)  # MB/s
            net_recv_rate = (net_io_after.bytes_recv - net_io_before.bytes_recv) / duration / (1024**2)  # MB/s
            net_sent_rate = (net_io_after.bytes_sent - net_io_before.bytes_sent) / duration / (1024**2)  # MB/s
            
            # Identify bottlenecks
            bottlenecks = []
            recommendations = []
            
            if avg_cpu > 80:
                bottlenecks.append("HIGH_CPU_USAGE")
                recommendations.append("CPU is heavily utilized. Consider upgrading CPU or optimizing running applications.")
            
            if avg_mem > 85:
                bottlenecks.append("HIGH_MEMORY_USAGE")
                recommendations.append("Memory usage is high. Consider adding more RAM or closing memory-intensive applications.")
            
            if disk_read_rate > 100 or disk_write_rate > 100:
                bottlenecks.append("HIGH_DISK_IO")
                recommendations.append("High disk I/O detected. Consider upgrading to SSD or optimizing disk-intensive operations.")
            
            # Get top resource consumers
            top_cpu_procs = []
            top_mem_procs = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 10:
                        top_cpu_procs.append({
                            "name": pinfo['name'],
                            "pid": pinfo['pid'],
                            "cpu_percent": pinfo['cpu_percent']
                        })
                    if pinfo['memory_percent'] > 5:
                        top_mem_procs.append({
                            "name": pinfo['name'],
                            "pid": pinfo['pid'],
                            "memory_percent": pinfo['memory_percent']
                        })
                except:
                    pass
            
            top_cpu_procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_mem_procs.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            diagnostics = {
                "duration_seconds": duration,
                "metrics": {
                    "cpu": {
                        "average_percent": round(avg_cpu, 2),
                        "max_percent": round(max_cpu, 2)
                    },
                    "memory": {
                        "average_percent": round(avg_mem, 2),
                        "max_percent": round(max_mem, 2)
                    },
                    "disk_io": {
                        "read_rate_mb_s": round(disk_read_rate, 2),
                        "write_rate_mb_s": round(disk_write_rate, 2)
                    },
                    "network_io": {
                        "receive_rate_mb_s": round(net_recv_rate, 2),
                        "send_rate_mb_s": round(net_sent_rate, 2)
                    }
                },
                "bottlenecks": bottlenecks,
                "recommendations": recommendations,
                "top_cpu_processes": top_cpu_procs[:5],
                "top_memory_processes": top_mem_procs[:5]
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(diagnostics, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_hardware_recommendations(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get hardware upgrade recommendations"""
        try:
            use_case = arguments.get("use_case", "general")
            
            # Get current system specs
            cpu_count = psutil.cpu_count(logical=False)
            total_ram = psutil.virtual_memory().total / (1024**3)
            
            # Get motherboard info (platform-specific)
            motherboard_info = self._get_motherboard_info()
            
            recommendations = {
                "current_specs": {
                    "cpu_cores": cpu_count,
                    "ram_gb": round(total_ram, 2),
                    "motherboard": motherboard_info
                },
                "upgrade_recommendations": []
            }
            
            # Use case specific recommendations
            if use_case == "gaming":
                if cpu_count < 6:
                    recommendations["upgrade_recommendations"].append({
                        "component": "CPU",
                        "reason": "Gaming benefits from 6+ cores for modern titles",
                        "suggestion": "Consider AMD Ryzen 5 5600X or Intel Core i5-12600K"
                    })
                if total_ram < 16:
                    recommendations["upgrade_recommendations"].append({
                        "component": "RAM",
                        "reason": "16GB minimum recommended for gaming",
                        "suggestion": "Upgrade to 16GB DDR4 3200MHz or higher"
                    })
                recommendations["upgrade_recommendations"].append({
                    "component": "GPU",
                    "reason": "Graphics card is crucial for gaming performance",
                    "suggestion": "Consider RTX 4060 Ti or RX 7700 XT for 1080p/1440p gaming"
                })
                
            elif use_case == "content_creation":
                if cpu_count < 8:
                    recommendations["upgrade_recommendations"].append({
                        "component": "CPU",
                        "reason": "Content creation benefits from 8+ cores",
                        "suggestion": "Consider AMD Ryzen 7 5800X or Intel Core i7-12700K"
                    })
                if total_ram < 32:
                    recommendations["upgrade_recommendations"].append({
                        "component": "RAM",
                        "reason": "32GB+ recommended for video editing and 3D rendering",
                        "suggestion": "Upgrade to 32GB DDR4 3600MHz"
                    })
                recommendations["upgrade_recommendations"].append({
                    "component": "Storage",
                    "reason": "Fast storage crucial for large file handling",
                    "suggestion": "Add NVMe SSD (Samsung 980 Pro or WD Black SN850)"
                })
                
            elif use_case == "development":
                if total_ram < 16:
                    recommendations["upgrade_recommendations"].append({
                        "component": "RAM",
                        "reason": "16GB+ recommended for running VMs and containers",
                        "suggestion": "Upgrade to 16GB or 32GB DDR4"
                    })
                recommendations["upgrade_recommendations"].append({
                    "component": "Storage",
                    "reason": "Fast storage improves build times",
                    "suggestion": "NVMe SSD for OS and development tools"
                })
                
            elif use_case == "productivity":
                if total_ram < 8:
                    recommendations["upgrade_recommendations"].append({
                        "component": "RAM",
                        "reason": "8GB minimum for smooth multitasking",
                        "suggestion": "Upgrade to 8GB or 16GB DDR4"
                    })
                recommendations["upgrade_recommendations"].append({
                    "component": "Storage",
                    "reason": "SSD significantly improves system responsiveness",
                    "suggestion": "Replace HDD with SATA SSD (Samsung 870 EVO or Crucial MX500)"
                })
            
            # General recommendations based on system analysis
            vm = psutil.virtual_memory()
            if vm.percent > 80:
                recommendations["upgrade_recommendations"].append({
                    "component": "RAM",
                    "reason": f"Current memory usage is {vm.percent}% - system would benefit from more RAM",
                    "suggestion": f"Add {16 if total_ram < 16 else 32}GB RAM"
                })
            
            # Check for SSD
            has_ssd = False
            for partition in psutil.disk_partitions():
                try:
                    if self.os_type == "Windows":
                        if self._get_windows_drive_type(partition.device) == "SSD":
                            has_ssd = True
                            break
                except:
                    pass
            
            if not has_ssd:
                recommendations["upgrade_recommendations"].append({
                    "component": "Storage",
                    "reason": "No SSD detected - SSD provides major performance improvement",
                    "suggestion": "Add 500GB+ NVMe or SATA SSD for OS and applications"
                })
            
            recommendations["compatibility_notes"] = [
                "Check motherboard compatibility before purchasing RAM (DDR3/DDR4/DDR5)",
                "Verify power supply wattage before GPU upgrade",
                "Ensure motherboard has M.2 slot for NVMe SSDs",
                "Consider case dimensions for GPU upgrades"
            ]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting hardware recommendations: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def get_computer_model(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get computer model and manufacturer information from the system"""
        try:
            include_details = arguments.get("include_details", True)
            
            # Get platform-specific computer model information
            if self.os_type == "Windows":
                info = self._get_windows_computer_model(include_details)
            elif self.os_type == "Darwin":
                info = self._get_macos_computer_model(include_details)
            else:  # Linux and other Unix-like systems
                info = self._get_linux_computer_model(include_details)
            
            # Add general system information
            info["system_info"] = {
                "platform": self.os_type,
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "hostname": platform.node()
            }
            
            # Format the output
            output = "# Computer Model Information\n\n"
            
            # Basic Information
            if info.get("basic_info"):
                output += "## Basic Information\n"
                for key, value in info["basic_info"].items():
                    if value and value != "Unknown" and value != "Not Available":
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # System Details
            if include_details and info.get("system_details"):
                output += "## System Details\n"
                for key, value in info["system_details"].items():
                    if value and value != "Unknown" and value != "Not Available":
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # Platform Information
            if info.get("system_info"):
                output += "## Platform Information\n"
                for key, value in info["system_info"].items():
                    if value:
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            return [types.TextContent(type="text", text=output)]
            
        except Exception as e:
            logger.error(f"Error getting computer model: {e}")
            return [types.TextContent(
                type="text", 
                text=f"Error retrieving computer model information: {str(e)}"
            )]
    
    async def get_motherboard_details(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get detailed motherboard information including manufacturer, model, BIOS, and hardware specifications"""
        try:
            include_bios = arguments.get("include_bios", True)
            include_slots = arguments.get("include_slots", True)
            
            # Get platform-specific motherboard details
            if self.os_type == "Windows":
                info = self._get_windows_motherboard_details(include_bios, include_slots)
            elif self.os_type == "Darwin":
                info = self._get_macos_motherboard_details(include_bios, include_slots)
            else:  # Linux and other Unix-like systems
                info = self._get_linux_motherboard_details(include_bios, include_slots)
            
            # Add general system information
            info["system_info"] = {
                "platform": self.os_type,
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "hostname": platform.node()
            }
            
            # Format the output
            output = "# Motherboard Details\n\n"
            
            # Basic Information
            if info.get("basic_info"):
                output += "## Basic Information\n"
                for key, value in info["basic_info"].items():
                    if value and value != "Unknown":
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # BIOS Information
            if include_bios and info.get("bios_info"):
                output += "## BIOS/UEFI Information\n"
                for key, value in info["bios_info"].items():
                    if value and value != "Unknown":
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # Memory Information
            if info.get("memory_info"):
                output += "## Memory Information\n"
                for key, value in info["memory_info"].items():
                    if key == "slots" and isinstance(value, list):
                        output += f"- **Memory Slots**: {len(value)} slots detected\n"
                        for i, slot in enumerate(value, 1):
                            if isinstance(slot, dict):
                                output += f"  - Slot {i}: {slot.get('description', 'Unknown')}"
                                if slot.get('size_gb', 0) > 0:
                                    output += f" ({slot['size_gb']} GB"
                                    if slot.get('clock_mhz', 0) > 0:
                                        output += f" @ {slot['clock_mhz']} MHz"
                                    output += ")"
                                output += "\n"
                    elif value and value != "Unknown":
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # System Information
            if info.get("system_info"):
                output += "## System Information\n"
                for key, value in info["system_info"].items():
                    if value:
                        output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            # Capabilities and Features
            if info.get("capabilities"):
                output += "## Capabilities and Features\n"
                for key, value in info["capabilities"].items():
                    if value and value != "Unknown":
                        if isinstance(value, list):
                            output += f"- **{key.replace('_', ' ').title()}**: {', '.join(value)}\n"
                        else:
                            output += f"- **{key.replace('_', ' ').title()}**: {value}\n"
                output += "\n"
            
            return [types.TextContent(type="text", text=output)]
            
        except Exception as e:
            logger.error(f"Error getting motherboard details: {e}")
            return [types.TextContent(
                type="text", 
                text=f"Error retrieving motherboard details: {str(e)}"
            )]

    def _get_windows_motherboard_details(self, include_bios: bool, include_slots: bool) -> Dict[str, Any]:
        """Get Windows motherboard details using WMI and fallback methods"""
        info = {
            "basic_info": {},
            "bios_info": {},
            "memory_info": {},
            "capabilities": {}
        }
        
        try:
            # Try WMI first
            c = wmi.WMI()
            
            # Get motherboard basic info
            for board in c.Win32_BaseBoard():
                info["basic_info"]["manufacturer"] = getattr(board, 'Manufacturer', 'Unknown')
                info["basic_info"]["product"] = getattr(board, 'Product', 'Unknown')
                info["basic_info"]["version"] = getattr(board, 'Version', 'Unknown')
                info["basic_info"]["serial_number"] = getattr(board, 'SerialNumber', 'Unknown')
                
                # Additional motherboard features
                if hasattr(board, 'ConfigOptions') and board.ConfigOptions:
                    info["capabilities"]["config_options"] = board.ConfigOptions
                break
            
            # Get BIOS info
            if include_bios:
                for bios in c.Win32_BIOS():
                    info["bios_info"]["manufacturer"] = getattr(bios, 'Manufacturer', 'Unknown')
                    info["bios_info"]["version"] = getattr(bios, 'Version', 'Unknown')
                    info["bios_info"]["release_date"] = getattr(bios, 'ReleaseDate', 'Unknown')
                    info["bios_info"]["smbios_version"] = getattr(bios, 'SMBIOSBIOSVersion', 'Unknown')
                    
                    # BIOS characteristics
                    if hasattr(bios, 'BiosCharacteristics'):
                        info["bios_info"]["characteristics"] = bios.BiosCharacteristics
                    break
            
            # Get memory information
            total_memory = 0
            memory_slots = []
            
            for memory in c.Win32_PhysicalMemory():
                capacity = getattr(memory, 'Capacity', 0)
                if capacity:
                    capacity_gb = int(capacity) / (1024**3)
                    total_memory += capacity_gb
                    
                    slot_info = {
                        "description": getattr(memory, 'Description', 'Unknown'),
                        "size_gb": round(capacity_gb, 2),
                        "speed_mhz": getattr(memory, 'Speed', 0),
                        "manufacturer": getattr(memory, 'Manufacturer', 'Unknown'),
                        "part_number": getattr(memory, 'PartNumber', 'Unknown').strip(),
                        "form_factor": self._get_memory_form_factor(getattr(memory, 'FormFactor', 0)),
                        "memory_type": self._get_memory_type(getattr(memory, 'MemoryType', 0))
                    }
                    memory_slots.append(slot_info)
            
            if total_memory > 0:
                info["memory_info"]["total_memory_gb"] = round(total_memory, 2)
            if memory_slots:
                info["memory_info"]["slots"] = memory_slots
            
            # Get processor info for socket type
            for processor in c.Win32_Processor():
                info["capabilities"]["cpu_socket"] = getattr(processor, 'SocketDesignation', 'Unknown')
                info["capabilities"]["cpu_manufacturer"] = getattr(processor, 'Manufacturer', 'Unknown')
                break
                
        except Exception as e:
            logger.warning(f"WMI failed, trying subprocess method: {e}")
            # Fallback to subprocess method
            info = self._get_windows_motherboard_via_subprocess(include_bios, include_slots)
        
        return info
    
    def _get_windows_motherboard_via_subprocess(self, include_bios: bool, include_slots: bool) -> Dict[str, Any]:
        """Get Windows motherboard details using subprocess and registry"""
        info = {
            "basic_info": {},
            "bios_info": {},
            "memory_info": {},
            "capabilities": {}
        }
        
        try:
            # Get motherboard info using wmic
            result = subprocess.run(
                ["wmic", "baseboard", "get", "Manufacturer,Product,Version,SerialNumber", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('Node'):
                        parts = line.split(',')
                        if len(parts) >= 5:
                            info["basic_info"]["manufacturer"] = parts[1].strip() or 'Unknown'
                            info["basic_info"]["product"] = parts[2].strip() or 'Unknown'
                            info["basic_info"]["serial_number"] = parts[3].strip() or 'Unknown'
                            info["basic_info"]["version"] = parts[4].strip() or 'Unknown'
                            break
            
            # Get BIOS info
            if include_bios:
                result = subprocess.run(
                    ["wmic", "bios", "get", "Manufacturer,Version,ReleaseDate,SMBIOSBIOSVersion", "/format:csv"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line and not line.startswith('Node'):
                            parts = line.split(',')
                            if len(parts) >= 5:
                                info["bios_info"]["manufacturer"] = parts[1].strip() or 'Unknown'
                                info["bios_info"]["release_date"] = parts[2].strip() or 'Unknown'
                                info["bios_info"]["smbios_version"] = parts[3].strip() or 'Unknown'
                                info["bios_info"]["version"] = parts[4].strip() or 'Unknown'
                                break
            
            # Get memory info
            result = subprocess.run(
                ["wmic", "memorychip", "get", "Capacity,Speed,Manufacturer,PartNumber,FormFactor,MemoryType", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total_memory = 0
                memory_slots = []
                
                for line in lines:
                    if line and not line.startswith('Node') and ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 7:
                            try:
                                capacity = int(parts[1]) if parts[1].strip() else 0
                                if capacity > 0:
                                    capacity_gb = capacity / (1024**3)
                                    total_memory += capacity_gb
                                    
                                    form_factor = int(parts[2]) if parts[2].strip().isdigit() else 0
                                    memory_type = int(parts[6]) if parts[6].strip().isdigit() else 0
                                    
                                    slot_info = {
                                        "description": "Memory Module",
                                        "size_gb": round(capacity_gb, 2),
                                        "speed_mhz": int(parts[5]) if parts[5].strip().isdigit() else 0,
                                        "manufacturer": parts[3].strip() or 'Unknown',
                                        "part_number": parts[4].strip() or 'Unknown',
                                        "form_factor": self._get_memory_form_factor(form_factor),
                                        "memory_type": self._get_memory_type(memory_type)
                                    }
                                    memory_slots.append(slot_info)
                            except (ValueError, IndexError):
                                continue
                
                if total_memory > 0:
                    info["memory_info"]["total_memory_gb"] = round(total_memory, 2)
                if memory_slots:
                    info["memory_info"]["slots"] = memory_slots
            
            # Try to get additional info from registry
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
                try:
                    bios_vendor, _ = winreg.QueryValueEx(key, "BIOSVendor")
                    if bios_vendor and not info["bios_info"].get("manufacturer"):
                        info["bios_info"]["manufacturer"] = bios_vendor
                except FileNotFoundError:
                    pass
                
                try:
                    bios_version, _ = winreg.QueryValueEx(key, "BIOSVersion")
                    if bios_version and not info["bios_info"].get("version"):
                        info["bios_info"]["version"] = bios_version
                except FileNotFoundError:
                    pass
                
                winreg.CloseKey(key)
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error in subprocess motherboard detection: {e}")
        
        return info
    
    def _get_memory_form_factor(self, form_factor: int) -> str:
        """Convert memory form factor code to readable string"""
        form_factors = {
            0: "Unknown",
            1: "Other",
            2: "SIP",
            3: "DIP", 
            4: "ZIP",
            5: "SOJ",
            6: "Proprietary",
            7: "SIMM",
            8: "DIMM",
            9: "TSOP",
            10: "PGA",
            11: "RIMM",
            12: "SODIMM",
            13: "SRIMM",
            14: "SMD",
            15: "SSMP",
            16: "QFP",
            17: "TQFP",
            18: "SOIC",
            19: "LCC",
            20: "PLCC",
            21: "BGA",
            22: "FPBGA",
            23: "LGA"
        }
        return form_factors.get(form_factor, f"Unknown ({form_factor})")
    
    def _get_memory_type(self, memory_type: int) -> str:
        """Convert memory type code to readable string"""
        memory_types = {
            0: "Unknown",
            1: "Other",
            2: "DRAM",
            3: "Synchronous DRAM",
            4: "Cache DRAM",
            5: "EDO",
            6: "EDRAM",
            7: "VRAM",
            8: "SRAM",
            9: "RAM",
            10: "ROM",
            11: "Flash",
            12: "EEPROM",
            13: "FEPROM",
            14: "EPROM",
            15: "CDRAM",
            16: "3DRAM",
            17: "SDRAM",
            18: "SGRAM",
            19: "RDRAM",
            20: "DDR",
            21: "DDR2",
            22: "DDR2 FB-DIMM",
            24: "DDR3",
            25: "FBD2",
            26: "DDR4",
            27: "LPDDR",
            28: "LPDDR2",
            29: "LPDDR3",
            30: "LPDDR4"
        }
        return memory_types.get(memory_type, f"Unknown ({memory_type})")
    
    def _get_macos_motherboard_details(self, include_bios: bool, include_slots: bool) -> Dict[str, Any]:
        """Get macOS motherboard details using system_profiler"""
        info = {
            "basic_info": {},
            "bios_info": {},
            "memory_info": {},
            "capabilities": {}
        }
        
        try:
            # Get hardware overview
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType", "-xml"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    import plistlib
                    data = plistlib.loads(result.stdout.encode())
                    
                    if data and len(data) > 0:
                        hardware_items = data[0].get('_items', [])
                        for item in hardware_items:
                            # Basic motherboard info (from Apple's perspective)
                            info["basic_info"]["manufacturer"] = "Apple Inc."
                            info["basic_info"]["product"] = item.get("machine_model", "Unknown")
                            info["basic_info"]["model_identifier"] = item.get("machine_name", "Unknown")
                            info["basic_info"]["serial_number"] = item.get("serial_number", "Unknown")
                            
                            # Memory information
                            memory_str = item.get("physical_memory", "")
                            if memory_str:
                                try:
                                    # Parse memory string like "16 GB"
                                    if "GB" in memory_str:
                                        memory_gb = float(memory_str.split()[0])
                                        info["memory_info"]["total_memory_gb"] = memory_gb
                                except:
                                    pass
                            
                            # CPU information
                            info["capabilities"]["cpu_type"] = item.get("cpu_type", "Unknown")
                            info["capabilities"]["number_processors"] = item.get("number_processors", "Unknown")
                            
                            # Boot ROM version (closest to BIOS info on Mac)
                            if include_bios:
                                info["bios_info"]["boot_rom_version"] = item.get("boot_rom_version", "Unknown")
                                info["bios_info"]["smc_version"] = item.get("SMC_version", "Unknown")
                            
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse system_profiler XML: {e}")
            
            # Get memory details if requested
            if include_slots:
                result = subprocess.run(
                    ["system_profiler", "SPMemoryDataType", "-xml"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        memory_data = plistlib.loads(result.stdout.encode())
                        if memory_data and len(memory_data) > 0:
                            memory_items = memory_data[0].get('_items', [])
                            memory_slots = []
                            
                            for item in memory_items:
                                if '_items' in item:  # Memory banks
                                    for bank in item['_items']:
                                        size_str = bank.get('dimm_size', '')
                                        if size_str and size_str != 'empty':
                                            try:
                                                if 'GB' in size_str:
                                                    size_gb = float(size_str.split()[0])
                                                elif 'MB' in size_str:
                                                    size_gb = float(size_str.split()[0]) / 1024
                                                else:
                                                    size_gb = 0
                                                
                                                slot_info = {
                                                    "description": bank.get('dimm_type', 'Unknown'),
                                                    "size_gb": size_gb,
                                                    "speed_mhz": bank.get('dimm_speed', 'Unknown'),
                                                    "manufacturer": bank.get('dimm_manufacturer', 'Unknown'),
                                                    "part_number": bank.get('dimm_part_number', 'Unknown'),
                                                    "status": bank.get('dimm_status', 'Unknown')
                                                }
                                                memory_slots.append(slot_info)
                                            except:
                                                pass
                            
                            if memory_slots:
                                info["memory_info"]["slots"] = memory_slots
                    except Exception as e:
                        logger.warning(f"Failed to parse memory data: {e}")
            
            # Get additional system information
            result = subprocess.run(
                ["system_profiler", "SPSoftwareDataType"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'System Version:' in line:
                        info["capabilities"]["system_version"] = line.split(':', 1)[1].strip()
                    elif 'Kernel Version:' in line:
                        info["capabilities"]["kernel_version"] = line.split(':', 1)[1].strip()
        
        except Exception as e:
            logger.error(f"Error getting macOS motherboard details: {e}")
        
        return info
    
    def _get_linux_motherboard_details(self, include_bios: bool, include_slots: bool) -> Dict[str, Any]:
        """Get Linux motherboard details"""
        info = {
            "basic_info": {},
            "bios_info": {},
            "memory_info": {},
            "capabilities": {}
        }
        
        try:
            # Try dmidecode first (requires sudo)
            result = subprocess.run(
                ["sudo", "-n", "dmidecode", "-t", "baseboard"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'Manufacturer:' in line:
                        info["basic_info"]["manufacturer"] = line.split(':', 1)[1].strip()
                    elif 'Product Name:' in line:
                        info["basic_info"]["product"] = line.split(':', 1)[1].strip()
                    elif 'Version:' in line:
                        info["basic_info"]["version"] = line.split(':', 1)[1].strip()
                    elif 'Serial Number:' in line:
                        info["basic_info"]["serial_number"] = line.split(':', 1)[1].strip()
            
            # Get BIOS info
            if include_bios:
                result = subprocess.run(
                    ["sudo", "-n", "dmidecode", "-t", "bios"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if 'Vendor:' in line:
                            info["bios_info"]["vendor"] = line.split(':', 1)[1].strip()
                        elif 'Version:' in line:
                            info["bios_info"]["version"] = line.split(':', 1)[1].strip()
                        elif 'Release Date:' in line:
                            info["bios_info"]["release_date"] = line.split(':', 1)[1].strip()
            
            # Fallback to /sys/devices if dmidecode fails
            if not info["basic_info"]:
                sys_paths = {
                    "manufacturer": "/sys/devices/virtual/dmi/id/board_vendor",
                    "product": "/sys/devices/virtual/dmi/id/board_name",
                    "version": "/sys/devices/virtual/dmi/id/board_version",
                    "serial_number": "/sys/devices/virtual/dmi/id/board_serial",
                    "bios_vendor": "/sys/devices/virtual/dmi/id/bios_vendor",
                    "bios_version": "/sys/devices/virtual/dmi/id/bios_version",
                    "bios_date": "/sys/devices/virtual/dmi/id/bios_date"
                }
                
                for key, path in sys_paths.items():
                    if os.path.exists(path):
                        try:
                            with open(path, 'r') as f:
                                value = f.read().strip()
                                if key.startswith('bios_'):
                                    info["bios_info"][key.replace('bios_', '')] = value
                                else:
                                    info["basic_info"][key] = value
                        except:
                            pass
            
            # Get memory information from /proc/meminfo
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            mem_kb = int(line.split()[1])
                            info["memory_info"]["total_memory_gb"] = round(mem_kb / (1024**2), 2)
                            break
            
            # Try lshw for additional details
            result = subprocess.run(
                ["lshw", "-C", "memory", "-json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                try:
                    memory_data = json.loads(result.stdout)
                    # Parse lshw output for memory slots
                    if isinstance(memory_data, list):
                        memory_slots = []
                        for item in memory_data:
                            if item.get('class') == 'memory' and 'bank' in item.get('id', ''):
                                slot_info = {
                                    "description": item.get('description', 'Unknown'),
                                    "size_gb": round(item.get('size', 0) / (1024**3), 2) if item.get('size') else 0,
                                    "clock_mhz": item.get('clock', 0) / 1000000 if item.get('clock') else 0
                                }
                                memory_slots.append(slot_info)
                        
                        if memory_slots:
                            info["memory_info"]["slots"] = memory_slots
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error getting Linux motherboard details: {e}")
        
        return info
    
    def _get_windows_computer_model(self, include_details: bool) -> Dict[str, Any]:
        """Get Windows computer model and manufacturer using WMI and fallback methods"""
        info = {
            "basic_info": {},
            "system_details": {}
        }
        
        try:
            # Try WMI first
            c = wmi.WMI()
            
            # Get computer system information
            for system in c.Win32_ComputerSystem():
                info["basic_info"]["manufacturer"] = getattr(system, 'Manufacturer', 'Unknown')
                info["basic_info"]["model"] = getattr(system, 'Model', 'Unknown')
                info["basic_info"]["name"] = getattr(system, 'Name', 'Unknown')
                
                if include_details:
                    info["system_details"]["domain"] = getattr(system, 'Domain', 'Unknown')
                    info["system_details"]["workgroup"] = getattr(system, 'Workgroup', 'Unknown')
                    info["system_details"]["total_physical_memory"] = getattr(system, 'TotalPhysicalMemory', 'Unknown')
                    info["system_details"]["system_type"] = getattr(system, 'SystemType', 'Unknown')
                    info["system_details"]["pc_system_type"] = getattr(system, 'PCSystemType', 'Unknown')
                break
            
            # Get additional system enclosure information
            if include_details:
                for enclosure in c.Win32_SystemEnclosure():
                    info["system_details"]["chassis_types"] = getattr(enclosure, 'ChassisTypes', 'Unknown')
                    info["system_details"]["serial_number"] = getattr(enclosure, 'SerialNumber', 'Unknown')
                    info["system_details"]["smbios_asset_tag"] = getattr(enclosure, 'SMBIOSAssetTag', 'Unknown')
                    break
                
                # Get computer system product information
                for product in c.Win32_ComputerSystemProduct():
                    info["system_details"]["uuid"] = getattr(product, 'UUID', 'Unknown')
                    info["system_details"]["identifying_number"] = getattr(product, 'IdentifyingNumber', 'Unknown')
                    info["system_details"]["sku_number"] = getattr(product, 'SKUNumber', 'Unknown')
                    info["system_details"]["version"] = getattr(product, 'Version', 'Unknown')
                    break
                
        except Exception as e:
            logger.warning(f"WMI failed, trying wmic fallback: {e}")
            # Fallback to wmic command
            info = self._get_windows_computer_model_via_wmic(include_details)
        
        return info
    
    def _get_windows_computer_model_via_wmic(self, include_details: bool) -> Dict[str, Any]:
        """Get Windows computer model using wmic command as fallback"""
        info = {
            "basic_info": {},
            "system_details": {}
        }
        
        try:
            # Get basic computer system info
            result = subprocess.run(
                ["wmic", "computersystem", "get", "Manufacturer,Model,Name,Domain,Workgroup,TotalPhysicalMemory,SystemType", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('Node'):
                        parts = line.split(',')
                        if len(parts) >= 8:
                            info["basic_info"]["manufacturer"] = parts[2].strip() or 'Unknown'
                            info["basic_info"]["model"] = parts[3].strip() or 'Unknown'
                            info["basic_info"]["name"] = parts[4].strip() or 'Unknown'
                            
                            if include_details:
                                info["system_details"]["domain"] = parts[1].strip() or 'Unknown'
                                info["system_details"]["workgroup"] = parts[8].strip() or 'Unknown'
                                info["system_details"]["total_physical_memory"] = parts[7].strip() or 'Unknown'
                                info["system_details"]["system_type"] = parts[6].strip() or 'Unknown'
                            break
            
            # Get additional details if requested
            if include_details:
                # Get system enclosure info
                result = subprocess.run(
                    ["wmic", "systemenclosure", "get", "ChassisTypes,SerialNumber,SMBIOSAssetTag", "/format:csv"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line and not line.startswith('Node'):
                            parts = line.split(',')
                            if len(parts) >= 4:
                                info["system_details"]["chassis_types"] = parts[1].strip() or 'Unknown'
                                info["system_details"]["serial_number"] = parts[2].strip() or 'Unknown'
                                info["system_details"]["smbios_asset_tag"] = parts[3].strip() or 'Unknown'
                                break
                
                # Get computer system product info
                result = subprocess.run(
                    ["wmic", "computersystemproduct", "get", "UUID,IdentifyingNumber,SKUNumber,Version", "/format:csv"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line and not line.startswith('Node'):
                            parts = line.split(',')
                            if len(parts) >= 5:
                                info["system_details"]["uuid"] = parts[4].strip() or 'Unknown'
                                info["system_details"]["identifying_number"] = parts[1].strip() or 'Unknown'
                                info["system_details"]["sku_number"] = parts[2].strip() or 'Unknown'
                                info["system_details"]["version"] = parts[3].strip() or 'Unknown'
                                break
            
        except Exception as e:
            logger.error(f"Error in wmic computer model detection: {e}")
        
        return info
    
    def _get_macos_computer_model(self, include_details: bool) -> Dict[str, Any]:
        """Get macOS computer model using system_profiler"""
        info = {
            "basic_info": {},
            "system_details": {}
        }
        
        try:
            # Get hardware overview
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType", "-xml"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    import plistlib
                    data = plistlib.loads(result.stdout.encode())
                    
                    if data and len(data) > 0:
                        hardware_items = data[0].get('_items', [])
                        for item in hardware_items:
                            # Basic computer info
                            info["basic_info"]["manufacturer"] = "Apple Inc."
                            info["basic_info"]["model"] = item.get("machine_model", "Unknown")
                            info["basic_info"]["name"] = item.get("machine_name", "Unknown")
                            
                            if include_details:
                                info["system_details"]["model_identifier"] = item.get("machine_name", "Unknown")
                                info["system_details"]["serial_number"] = item.get("serial_number", "Unknown")
                                info["system_details"]["hardware_uuid"] = item.get("platform_UUID", "Unknown")
                                info["system_details"]["boot_rom_version"] = item.get("boot_rom_version", "Unknown")
                                info["system_details"]["smc_version"] = item.get("SMC_version", "Unknown")
                                info["system_details"]["cpu_type"] = item.get("cpu_type", "Unknown")
                                info["system_details"]["number_processors"] = item.get("number_processors", "Unknown")
                                info["system_details"]["physical_memory"] = item.get("physical_memory", "Unknown")
                            break
                except Exception as e:
                    logger.warning(f"Failed to parse system_profiler XML: {e}")
            
            # Fallback to text format if XML parsing fails
            if not info["basic_info"]:
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    info["basic_info"]["manufacturer"] = "Apple Inc."
                    
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if 'Model Name:' in line:
                            info["basic_info"]["model"] = line.split(':', 1)[1].strip()
                        elif 'Model Identifier:' in line:
                            info["basic_info"]["name"] = line.split(':', 1)[1].strip()
                            if include_details:
                                info["system_details"]["model_identifier"] = line.split(':', 1)[1].strip()
                        elif include_details:
                            if 'Serial Number:' in line:
                                info["system_details"]["serial_number"] = line.split(':', 1)[1].strip()
                            elif 'Hardware UUID:' in line:
                                info["system_details"]["hardware_uuid"] = line.split(':', 1)[1].strip()
                            elif 'Boot ROM Version:' in line:
                                info["system_details"]["boot_rom_version"] = line.split(':', 1)[1].strip()
                            elif 'SMC Version:' in line:
                                info["system_details"]["smc_version"] = line.split(':', 1)[1].strip()
                            elif 'Processor Name:' in line:
                                info["system_details"]["cpu_type"] = line.split(':', 1)[1].strip()
                            elif 'Number of Processors:' in line:
                                info["system_details"]["number_processors"] = line.split(':', 1)[1].strip()
                            elif 'Memory:' in line:
                                info["system_details"]["physical_memory"] = line.split(':', 1)[1].strip()
            
        except Exception as e:
            logger.error(f"Error getting macOS computer model: {e}")
        
        return info
    
    def _get_linux_computer_model(self, include_details: bool) -> Dict[str, Any]:
        """Get Linux computer model using dmidecode and /sys/devices fallback"""
        info = {
            "basic_info": {},
            "system_details": {}
        }
        
        try:
            # Try dmidecode first (requires sudo for full access)
            result = subprocess.run(
                ["sudo", "-n", "dmidecode", "-t", "system"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'Manufacturer:' in line:
                        info["basic_info"]["manufacturer"] = line.split(':', 1)[1].strip()
                    elif 'Product Name:' in line:
                        info["basic_info"]["model"] = line.split(':', 1)[1].strip()
                    elif 'Version:' in line:
                        info["basic_info"]["name"] = line.split(':', 1)[1].strip()
                    elif include_details:
                        if 'Serial Number:' in line:
                            info["system_details"]["serial_number"] = line.split(':', 1)[1].strip()
                        elif 'UUID:' in line:
                            info["system_details"]["uuid"] = line.split(':', 1)[1].strip()
                        elif 'SKU Number:' in line:
                            info["system_details"]["sku_number"] = line.split(':', 1)[1].strip()
                        elif 'Family:' in line:
                            info["system_details"]["family"] = line.split(':', 1)[1].strip()
            
            # If dmidecode didn't work or didn't provide enough info, try /sys/devices fallback
            if not info["basic_info"]:
                sys_paths = {
                    "manufacturer": "/sys/devices/virtual/dmi/id/sys_vendor",
                    "model": "/sys/devices/virtual/dmi/id/product_name",
                    "name": "/sys/devices/virtual/dmi/id/product_version",
                    "serial_number": "/sys/devices/virtual/dmi/id/product_serial",
                    "uuid": "/sys/devices/virtual/dmi/id/product_uuid",
                    "sku_number": "/sys/devices/virtual/dmi/id/product_sku",
                    "family": "/sys/devices/virtual/dmi/id/product_family"
                }
                
                for key, path in sys_paths.items():
                    if os.path.exists(path):
                        try:
                            with open(path, 'r') as f:
                                value = f.read().strip()
                                if value and value != "Not Specified":
                                    if key in ["manufacturer", "model", "name"]:
                                        info["basic_info"][key] = value
                                    elif include_details:
                                        info["system_details"][key] = value
                        except:
                            pass
            
            # Get additional system information if available
            if include_details:
                # Try to get hostname
                try:
                    with open('/proc/sys/kernel/hostname', 'r') as f:
                        info["system_details"]["hostname"] = f.read().strip()
                except:
                    pass
                
                # Try to get kernel version
                try:
                    with open('/proc/version', 'r') as f:
                        info["system_details"]["kernel_version"] = f.read().strip()
                except:
                    pass
                
                # Try to get distribution information
                try:
                    if os.path.exists('/etc/os-release'):
                        with open('/etc/os-release', 'r') as f:
                            for line in f:
                                if line.startswith('PRETTY_NAME='):
                                    info["system_details"]["distribution"] = line.split('=', 1)[1].strip().strip('"')
                                    break
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error getting Linux computer model: {e}")
        
        return info


async def main():
    """Main entry point"""
    logger.info("Starting System Diagnostics MCP Server")
    server = SystemDiagnosticsServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
