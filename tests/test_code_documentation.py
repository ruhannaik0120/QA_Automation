"""Enforce structural documentation requirements across project Python code.

The suite checks module and definition docstrings plus balanced collapsible
regions. It validates source structure only and imports no application module.
"""

# region Imports and module setup
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOTS = (REPOSITORY_ROOT / "MCP", REPOSITORY_ROOT / "modules", REPOSITORY_ROOT / "tests")
IGNORED_PARTS = {".pytest_cache", ".pytest-tmp", "__pycache__"}
REGION_START = re.compile(r"^\s*#\s*region\b", re.IGNORECASE)
REGION_END = re.compile(r"^\s*#\s*endregion\b", re.IGNORECASE)
# endregion Imports and module setup


# region Function: Python source paths
def _python_source_paths() -> list[Path]:
    """Return project Python files while excluding generated cache directories."""

    return sorted(
        path
        for root in PYTHON_ROOTS
        for path in root.rglob("*.py")
        if not any(part in IGNORED_PARTS for part in path.parts)
    )
# endregion Function: Python source paths


# region Function: Definition nodes
def _definition_nodes(tree: ast.AST) -> list[ast.AST]:
    """Return every class and synchronous or asynchronous function node."""

    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
# endregion Function: Definition nodes


# region Function: Executable entry-point nodes
def _entry_point_nodes(tree: ast.Module) -> list[ast.If]:
    """Return module-level guards that execute a Python file as a command."""

    return [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "__name__"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    ]
# endregion Function: Executable entry-point nodes


# region Function: Region immediately precedes
def _region_immediately_precedes(node: ast.AST, lines: list[str]) -> bool:
    """Check for a nearby region marker before a definition or its decorators."""

    decorator_lines = [decorator.lineno for decorator in getattr(node, "decorator_list", [])]
    first_code_line = min([node.lineno, *decorator_lines])
    preceding = lines[max(0, first_code_line - 6) : first_code_line - 1]
    return any(REGION_START.match(line) for line in preceding)
# endregion Function: Region immediately precedes


# region Function: Test Python code documentation convention
@pytest.mark.parametrize("path", _python_source_paths(), ids=lambda path: str(path.relative_to(REPOSITORY_ROOT)))
def test_python_code_documentation_convention(path: Path):
    """Verify every Python code block has collapsible regions and documentation."""

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source)

    assert ast.get_docstring(tree), f"Missing module docstring: {path}"
    assert sum(bool(REGION_START.match(line)) for line in lines) == sum(
        bool(REGION_END.match(line)) for line in lines
    ), f"Unbalanced regions: {path}"

    executable_nodes = tree.body[1:] if tree.body and ast.get_docstring(tree) else tree.body
    if executable_nodes:
        assert "# region Imports and module setup" in source, f"Missing module setup region: {path}"

    for node in _definition_nodes(tree):
        assert ast.get_docstring(node), f"Missing docstring for {node.name} in {path}:{node.lineno}"
        assert _region_immediately_precedes(node, lines), (
            f"Missing collapsible region for {node.name} in {path}:{node.lineno}"
        )

    for node in _entry_point_nodes(tree):
        assert _region_immediately_precedes(node, lines), (
            f"Missing collapsible region for executable entry point in {path}:{node.lineno}"
        )
# endregion Function: Test Python code documentation convention


# region Function: Test PowerShell region balance
def test_powershell_region_balance():
    """Verify every PowerShell utility uses balanced collapsible regions."""

    paths = sorted((REPOSITORY_ROOT / "MCP" / "scripts").glob("*.ps1"))
    assert paths, "No PowerShell utilities were found."
    for path in paths:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        starts = sum(bool(REGION_START.match(line)) for line in lines)
        ends = sum(bool(REGION_END.match(line)) for line in lines)
        assert starts > 0, f"Missing collapsible regions: {path}"
        assert starts == ends, f"Unbalanced regions: {path}"
# endregion Function: Test PowerShell region balance
