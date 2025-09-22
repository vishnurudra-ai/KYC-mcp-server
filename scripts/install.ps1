Write-Host "System Diagnostics MCP Server Installation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Error "Python 3.8 or higher is required"
            exit 1
        }
        Write-Host "✓ Python version check passed: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install Windows-specific dependencies
Write-Host "Installing Windows-specific dependencies..." -ForegroundColor Yellow
pip install wmi pywin32

# Run tests
Write-Host "Running basic tests..." -ForegroundColor Yellow
python -m pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Some tests failed"
}

# Setup configuration
Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Activate the virtual environment: .\venv\Scripts\Activate.ps1"
Write-Host "2. Configure Claude Desktop (see README.md)"
Write-Host "3. Test the server: python -m system_diagnostics_mcp.server"
Write-Host ""

# Detect Claude Desktop config location
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"
Write-Host "Claude Desktop config location: $configPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "Configuration example saved to claude_config_example.json" -ForegroundColor Cyan

$currentPath = (Get-Location).Path
$pythonPath = "$currentPath\venv\Scripts\python.exe"

# Create a configuration example file
$configExample = @"
{
  "mcpServers": {
    "system-diagnostics": {
      "command": "$($pythonPath -replace '\\', '\\')",
      "args": ["-m", "system_diagnostics_mcp.server"],
      "cwd": "$($currentPath -replace '\\', '\\')",
      "env": {
        "PYTHONPATH": "$($currentPath -replace '\\', '\\')"
      }
    }
  }
}
"@

$configExample | Out-File -FilePath "claude_config_example.json" -Encoding UTF8
Write-Host "Configuration example created: claude_config_example.json"