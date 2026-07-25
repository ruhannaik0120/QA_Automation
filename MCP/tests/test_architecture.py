"""Protect the architectural boundary between drivers, connectors, and tools.

These source-level tests prevent database imports or driver calls from drifting
into services and MCP wrappers, where they would bypass shared policy.
"""

# region Imports and module setup
import ast
from pathlib import Path

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
