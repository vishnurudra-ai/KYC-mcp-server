#!/bin/bash

echo "System Diagnostics MCP Server Installation"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "Error: Python 3.8 or higher is required"
    exit 1
fi

echo "✓ Python version check passed: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Platform-specific installations
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected - installing macOS-specific dependencies..."
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux detected - checking for additional requirements..."
fi

# Run tests
echo "Running basic tests..."
python -m pytest tests/ -v --tb=short || echo "Warning: Some tests failed"

# Setup configuration
echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Configure Claude Desktop (see README.md)"
echo "3. Test the server: python -m system_diagnostics_mcp.server"
echo ""

# Detect Claude Desktop config location
if [[ "$OSTYPE" == "darwin"* ]]; then
    config_path="~/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    config_path="~/.config/Claude/claude_desktop_config.json"
fi

if [ -n "$config_path" ]; then
    echo "Claude Desktop config location: $config_path"
    echo ""
    echo "Add this to your config:"
    echo '{'
    echo '  "mcpServers": {'
    echo '    "system-diagnostics": {'
    echo "      \"command\": \"$(pwd)/venv/bin/python\","
    echo '      "args": ["-m", "system_diagnostics_mcp.server"],'
    echo "      \"cwd\": \"$(pwd)\","
    echo '      "env": {'
    echo "        \"PYTHONPATH\": \"$(pwd)\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo '}'
fi