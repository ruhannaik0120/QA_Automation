"""Resolve configured database types to lazily imported connector classes.

The registry is the only shared location that maps profile names to backend
modules. Lazy loading keeps optional database drivers isolated and ensures the
service layer depends only on the neutral connector contract.
"""

# region Imports and module setup
from __future__ import annotations

from importlib import import_module

from connectors.base import DatabaseConnector

SUPPORTED_CONNECTORS: dict[str, str] = {
    "demo": "connectors.demo.connector",
    "sqlserver": "connectors.sqlserver.connector",
    "mysql": "connectors.mysql.connector",
    "postgresql": "connectors.postgresql.connector",
    "snowflake": "connectors.snowflake.connector",
}
# endregion Imports and module setup


# region Class: ConnectorFactory
class ConnectorFactory:
    """Create registered connectors without leaking driver concerns upstream.

    The factory has no connection lifecycle of its own; callers own the
    returned connector and must close or replace it during runtime switching.
    """

    # region Function: Supported connectors
    @staticmethod
    def supported_connectors() -> tuple[str, ...]:
        """Return registered connector names in deterministic display order."""

        return tuple(sorted(SUPPORTED_CONNECTORS))
    # endregion Function: Supported connectors

    # region Function: Create
    @staticmethod
    def create(connector_type: str | None = None) -> DatabaseConnector:
        """Build the requested connector, falling back to runtime configuration."""

        # Normalization makes profile and environment values case-insensitive.
        connector_name = (connector_type or "").strip().lower()
        if not connector_name:
            from config import Config

            connector_name = Config.DB_TYPE.strip().lower()

        if not connector_name:
            raise ValueError("DB_TYPE is required to select a connector.")

        module_path = SUPPORTED_CONNECTORS.get(connector_name)
        if module_path is None:
            supported = ", ".join(ConnectorFactory.supported_connectors())
            raise ValueError(
                f"Unsupported connector type: {connector_name}. Supported values: {supported}."
            )

        # Lazy imports isolate optional drivers: using PostgreSQL should not
        # require importing Snowflake or SQL Server dependencies at startup.
        module = import_module(module_path)
        # Every connector exports the same alias, so adding a backend requires
        # one registry entry and no changes to the service or MCP tool layers.
        connector_class = getattr(module, "Connector", None)
        if connector_class is None:
            raise ValueError(
                f"Connector module {module_path} must expose Connector."
            )

        return connector_class()
    # endregion Function: Create
# endregion Class: ConnectorFactory
