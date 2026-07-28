"""Protect the architectural boundary between drivers, connectors, and tools.

These source-level tests prevent database imports or driver calls from drifting
into services and MCP wrappers, where they would bypass shared policy.
"""

# region Imports and module setup
import ast
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DRIVER_MODULES = {"pyodbc", "mysql", "psycopg", "snowflake"}
# endregion Imports and module setup


# region Function: Test database drivers are imported only by connectors
def test_database_drivers_are_imported_only_by_connectors():
    """Prevent tools and services from bypassing connector boundaries."""

    violations: list[str] = []
    for path in ROOT.rglob("*.py"):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {"connectors", ".venv"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = {node.module.split(".")[0]}
            else:
                continue
            if modules & FORBIDDEN_DRIVER_MODULES:
                violations.append(f"{relative}:{node.lineno}")
    assert not violations, "Database drivers imported outside connectors/: " + ", ".join(violations)
# endregion Function: Test database drivers are imported only by connectors


# region Function: Test MCP SDK remains FastMCP compatible
def test_mcp_sdk_remains_fastmcp_compatible():
    """Keep fresh installs on the SDK major used by the server entry point."""

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    mcp_requirements = [line.strip() for line in requirements if line.strip().startswith("mcp")]

    assert mcp_requirements == ["mcp>=1.28.0,<2"]
# endregion Function: Test MCP SDK remains FastMCP compatible


# region Function: Test setup gates verify FastMCP import
def test_setup_gates_verify_fastmcp_import():
    """Require setup and full verification to test the server's exact SDK API."""

    exact_import = "from mcp.server.fastmcp import FastMCP"
    for relative_path in ("scripts/setup.ps1", "scripts/verify.ps1"):
        script = (ROOT / relative_path).read_text(encoding="utf-8")
        assert exact_import in script
        assert "metadata.version('mcp')" in script
# endregion Function: Test setup gates verify FastMCP import


# region Function: Test server imports with supported SDK
def test_server_imports_with_supported_sdk():
    """Import the real server module with deterministic non-secret demo settings."""

    environment = os.environ.copy()
    environment.update(
        {
            "DB_TYPE": "demo",
            "DB_HOST": "demo-local",
            "DB_DATABASE": "qa_demo",
            "DB_USERNAME": "",
            "DB_PASSWORD": "",
            "DB_CONNECTION_OPTIONS": "{}",
            "DB_ACTIVE_PROFILE": "demo-local",
        }
    )
    result = subprocess.run(
        [sys.executable, "-c", "import server"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
# endregion Function: Test server imports with supported SDK
