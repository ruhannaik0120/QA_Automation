<#
Creates the workspace virtual environment and installs all Python dependencies.
The script is repeatable: an existing healthy environment is reused, while a
broken interpreter is replaced before installation continues.
#>

#region Script execution settings
$ErrorActionPreference = "Stop"
#endregion Script execution settings

#region Workspace path resolution
# Resolve paths from the script location so setup works from any current folder.
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = Split-Path -Parent $ProjectRoot
$Venv = Join-Path $WorkspaceRoot ".venv"
#endregion Workspace path resolution

#region Existing virtual environment validation
if (Test-Path $Venv) {
    # Validate the existing interpreter instead of assuming the folder is usable.
    $Python = Join-Path $Venv "Scripts\python.exe"
    $VenvHealthy = $false
    if (Test-Path $Python) {
        & $Python --version *> $null
        $VenvHealthy = $LASTEXITCODE -eq 0
    }
    if (-not $VenvHealthy) {
        Remove-Item -Recurse -Force $Venv
    }
}
#endregion Existing virtual environment validation

#region Virtual environment creation
if (-not (Test-Path $Venv)) {
    # Prefer the documented Python 3.12 runtime, then another Python 3 runtime.
    $Launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($Launcher) {
        & py -3.12 -m venv $Venv
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Python 3.12 was not found; trying the default Python 3 installation."
            & py -3 -m venv $Venv
        }
        if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment with py." }
    } else {
        $PythonCommand = Get-Command python -ErrorAction Stop
        & $PythonCommand.Source -m venv $Venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create the virtual environment with python." }
    }
}
#endregion Virtual environment creation

#region Dependency installation
$Python = Join-Path $Venv "Scripts\python.exe"
# Install with the virtual-environment interpreter to avoid global packages.
& $Python -m pip install "pip>=26.1.2"
if ($LASTEXITCODE -ne 0) { throw "Failed to install the minimum secure pip version." }
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install database MCP dependencies." }
& $Python -m pip install -r (Join-Path $WorkspaceRoot "requirements-e2e.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install E2E helper dependencies." }

#region MCP SDK compatibility verification
# Verify the exact v1 API imported by server.py so an incompatible major SDK
# cannot leave setup reporting a usable environment.
$FastMCPCompatibilityCheck = @'
import importlib.metadata as metadata
from mcp.server.fastmcp import FastMCP

print('MCP version:', metadata.version('mcp'))
print('FastMCP import OK')
'@
& $Python -c $FastMCPCompatibilityCheck
if ($LASTEXITCODE -ne 0) {
    throw "The installed MCP SDK is incompatible with MCP\server.py."
}
#endregion MCP SDK compatibility verification

Write-Host "Environment ready: $Python"
#endregion Dependency installation
