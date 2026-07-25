"""Define the backend-neutral connector contract used by MCP services.

Concrete connectors translate this interface into vendor-driver operations.
The contract keeps connection ownership, result shaping, and cleanup consistent
while SQL authorization and response envelopes remain in the service layer.
"""

# region Imports and module setup
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
# endregion Imports and module setup


# region Function: Unique column names
def unique_column_names(columns: list[object]) -> list[str]:
    """Return deterministic JSON keys without dropping duplicate result columns."""

    used: set[str] = set()
    normalized: list[str] = []
    for raw_name in columns:
        base_name = str(raw_name)
        candidate = base_name
        suffix = 2
        while candidate in used:
            candidate = f"{base_name}_{suffix}"
            suffix += 1
        used.add(candidate)
        normalized.append(candidate)
    return normalized
# endregion Function: Unique column names


# region Class: DatabaseConnector
class DatabaseConnector(ABC):
    """Stable contract implemented by every database backend.

    The MCP tools and service layer depend on this interface rather than a
    vendor driver. Consequently, adding another backend normally means adding
    one connector implementation and one factory registration while leaving
    the shared execution, logging, response, and profile-switching code intact.
    """

    # region Function: Connect
    @abstractmethod
    def connect(self, database: str | None = None, timeout_seconds: int | None = None) -> Any:
        """Open and return a driver connection for the requested database.

        Implementations apply the active profile and optional timeout. Driver
        exceptions are allowed to propagate for service-layer normalization.
        """
    # endregion Function: Connect

    # region Function: Test connection
    @abstractmethod
    def test_connection(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Run a lightweight connection check and return diagnostics."""
    # endregion Function: Test connection

    # region Function: Health check
    @abstractmethod
    def health_check(self, database: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Return a health/diagnostic summary for the connector."""
    # endregion Function: Health check

    # region Function: List databases
    @abstractmethod
    def list_databases(self, timeout_seconds: int | None = None) -> dict[str, Any]:
        """Return a list of available databases for the current connector."""
    # endregion Function: List databases

    # region Function: List tables
    @abstractmethod
    def list_tables(
        self,
        database: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Return normalized table metadata for the database and optional schema.

        The result must remain serializable and must not expose connection
        credentials or backend-specific connection objects.
        """
    # endregion Function: List tables

    # region Function: Describe table
    @abstractmethod
    def describe_table(
        self,
        database: str | None = None,
        table: str | None = None,
        schema: str | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Return normalized column metadata for one fully identified table.

        Implementations may apply backend naming rules, but must leave missing
        or invalid object handling to explicit errors rather than guessing.
        """
    # endregion Function: Describe table

    # region Function: Execute query
    @abstractmethod
    def execute_query(
        self,
        query: str,
        *,
        database: str | None = None,
        timeout_seconds: int | None = None,
        max_rows: int | None = None,
    ) -> Any:
        """Execute a database query and return the result payload."""
    # endregion Function: Execute query

    # region Function: Close
    @abstractmethod
    def close(self) -> None:
        """Close any open resources held by the connector."""
    # endregion Function: Close
# endregion Class: DatabaseConnector
