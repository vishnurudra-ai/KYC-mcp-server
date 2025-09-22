# System Diagnostics MCP Server

### Know Your Computer (KYC) MCP Server
Comprehensive system diagnostics and monitoring server providing detailed hardware information, performance metrics, and optimization recommendations.
- Tools: 12 diagnostic tools including CPU, memory, storage, network, processes, applications, battery, motherboard details, and performance analysis
- Resources: System metrics, hardware specifications, and real-time monitoring data
- Platform: Cross-platform (Windows, macOS, Linux)
- [Repository](https://github.com/vishnurudra-ai/KYC-mcp-server)
  
## Features

### Core Monitoring Capabilities
- **System Information**: OS detection, hardware specs, uptime
- **Computer Model Detection**: Manufacturer, model, system specifications
- **Motherboard Details**: Motherboard info, BIOS/UEFI, memory slots, hardware capabilities
- **CPU Metrics**: Usage, frequency, temperature, per-core statistics
- **Memory Monitoring**: RAM/swap usage, process memory consumption
- **Storage Analysis**: Disk usage, I/O stats, SSD/HDD detection
- **Network Monitoring**: Interface stats, active connections, traffic analysis
- **Process Management**: Running processes, resource consumption
- **Application Inventory**: Installed applications listing
- **Battery Status**: Power consumption, battery health (laptops)
- **System Logs**: Event logs, system messages
- **Performance Diagnostics**: Bottleneck detection, performance analysis
- **Hardware Recommendations**: Upgrade suggestions based on usage patterns

### Platform Support
- ✅ Windows (10, 11)
- ✅ macOS (10.15+)
- ✅ Linux (Ubuntu, Debian, RHEL, etc.)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/system-diagnostics-mcp.git
cd system-diagnostics-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Windows Additional Setup

For Windows systems, install additional dependencies:
```bash
pip install wmi pywin32
```

## Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

#### Windows
Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-diagnostics": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "system_diagnostics_mcp.server"],
      "cwd": "C:\\path\\to\\system-diagnostics-mcp",
      "env": {
        "PYTHONPATH": "C:\\path\\to\\system-diagnostics-mcp"
      }
    }
  }
}
```

#### macOS
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-diagnostics": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "system_diagnostics_mcp.server"],
      "cwd": "/path/to/system-diagnostics-mcp",
      "env": {
        "PYTHONPATH": "/path/to/system-diagnostics-mcp"
      }
    }
  }
}
```

#### Linux
Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-diagnostics": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "system_diagnostics_mcp.server"],
      "cwd": "/path/to/system-diagnostics-mcp",
      "env": {
        "PYTHONPATH": "/path/to/system-diagnostics-mcp"
      }
    }
  }
}
```

## Usage Examples

Once configured, you can interact with the system diagnostics server through Claude:

### Basic System Check
```
"What's my current system status?"
"Show me CPU and memory usage"
"How much disk space do I have left?"
```

### Performance Analysis
```
"My system is running slow, can you diagnose why?"
"Which applications are using the most memory?"
"Are there any performance bottlenecks?"
```

### Battery and Power (Laptops)
```
"Why is my battery draining so fast?"
"Which apps are consuming the most power?"
"What's my current battery status?"
```

### Hardware Recommendations
```
"I want to upgrade my system for gaming, what should I upgrade?"
"What hardware changes would improve my development workflow?"
"Should I add more RAM or upgrade my CPU?"
```

### Application Management
```
"What applications are installed on my system?"
"Show me all running processes sorted by CPU usage"
"Which processes are using network bandwidth?"
```

### Hardware and System Information
```
"What motherboard do I have?"
"What's my computer model and manufacturer?"
"How many RAM slots does my motherboard have?"
"What's the maximum RAM my system supports?"
"What BIOS version am I running?"
"Can I add more RAM to my system?"
"What memory slots are currently occupied?"
"Show me my motherboard specifications"
"What's my system's serial number?"
"What type of memory does my system use (DDR3/DDR4/DDR5)?"
```

## Available Tools

| Tool Name | Description |
|-----------|-------------|
| `get_system_info` | Comprehensive system information |
| `get_computer_model` | Computer manufacturer, model, and system details |
| `get_motherboard_details` | Motherboard specifications, BIOS info, and memory slots |
| `get_cpu_metrics` | Detailed CPU metrics and temperature |
| `get_memory_metrics` | Memory usage and top consumers |
| `get_storage_metrics` | Storage devices and usage |
| `get_network_metrics` | Network interfaces and connections |
| `get_processes` | Running processes information |
| `get_installed_applications` | List of installed applications |
| `get_battery_status` | Battery and power information |
| `get_system_logs` | Recent system logs and events |
| `diagnose_performance` | Performance analysis and bottlenecks |
| `get_hardware_recommendations` | Hardware upgrade suggestions |

## Permissions

Some features may require elevated permissions:

- **Windows**: Run as Administrator for complete system access
- **macOS**: Grant Terminal/Python full disk access in System Preferences
- **Linux**: Some features may require sudo access

## Troubleshooting

### Common Issues

1. **ImportError for psutil**
   ```bash
   pip install --upgrade psutil
   ```

2. **Windows: WMI errors**
   ```bash
   pip install --upgrade wmi pywin32
   ```

3. **Permission denied errors**
   - Run with appropriate privileges
   - Check file system permissions

4. **MCP connection issues**
   - Verify the path in Claude Desktop config
   - Ensure Python virtual environment is activated
   - Check that the server starts without errors

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Security Considerations

- The server has read-only access to system information
- No sensitive data (passwords, keys) is collected
- Network monitoring shows only connection metadata
- Application listing doesn't include user data

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built on the Model Context Protocol (MCP) by Anthropic
- Uses psutil for cross-platform system monitoring
- Inspired by various system monitoring tools" 
