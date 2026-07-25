"""Verify connector registry selection and lazy backend construction.

The tests ensure supported names remain deterministic and unsupported profile
values fail before optional driver modules are used.
"""

# region Imports and module setup
from connectors.base import DatabaseConnector
from connectors.demo.connector import DemoConnector
from connectors.factory import ConnectorFactory, SUPPORTED_CONNECTORS
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.sqlserver.connector import SQLServerConnector
from config import Config
import pytest


# Registry discovery feeds diagnostics and profile-switch validation.
# endregion Imports and module setup

# region Function: Test factory lists supported connectors
def test_factory_lists_supported_connectors():
    """Verify factory lists supported connectors."""
    assert "demo" in ConnectorFactory.supported_connectors()
    assert set(ConnectorFactory.supported_connectors()) == set(SUPPORTED_CONNECTORS)
# endregion Function: Test factory lists supported connectors


# Omitted selection deliberately falls back to the configured DB_TYPE.
# region Function: Test factory returns sqlserver connector by default
def test_factory_returns_sqlserver_connector_by_default():
    """Verify factory returns sqlserver connector by default."""
    Config.DB_TYPE = "sqlserver"
    connector = ConnectorFactory.create()

    assert isinstance(connector, DatabaseConnector)
    assert isinstance(connector, SQLServerConnector)
# endregion Function: Test factory returns sqlserver connector by default


# Explicit selections must construct their matching concrete implementation.
# region Function: Test factory returns mysql connector for mysql type
def test_factory_returns_mysql_connector_for_mysql_type():
    """Verify factory returns mysql connector for mysql type."""
    connector = ConnectorFactory.create("mysql")

    assert isinstance(connector, DatabaseConnector)
    assert connector.__class__.__name__ == "MySQLConnector"
# endregion Function: Test factory returns mysql connector for mysql type


# region Function: Test factory returns postgresql connector for postgresql type
def test_factory_returns_postgresql_connector_for_postgresql_type():
    """Verify factory returns postgresql connector for postgresql type."""
    connector = ConnectorFactory.create("postgresql")

    assert isinstance(connector, DatabaseConnector)
    assert isinstance(connector, PostgreSQLConnector)
# endregion Function: Test factory returns postgresql connector for postgresql type


# region Function: Test factory returns snowflake connector for snowflake type
def test_factory_returns_snowflake_connector_for_snowflake_type():
    """Verify factory returns snowflake connector for snowflake type."""
    connector = ConnectorFactory.create("snowflake")

    assert isinstance(connector, DatabaseConnector)
    assert connector.__class__.__name__ == "SnowflakeConnector"
# endregion Function: Test factory returns snowflake connector for snowflake type


# region Function: Test factory returns demo connector for demo type
def test_factory_returns_demo_connector_for_demo_type():
    """Verify factory returns demo connector for demo type."""
    connector = ConnectorFactory.create("demo")

    assert isinstance(connector, DemoConnector)
# endregion Function: Test factory returns demo connector for demo type


# Unknown names fail at the factory boundary, before any driver is imported.
# region Function: Test factory rejects invalid connector type
def test_factory_rejects_invalid_connector_type():
    """Verify factory rejects invalid connector type."""
    with pytest.raises(ValueError, match="Unsupported connector type"):
        ConnectorFactory.create("oracle")
# endregion Function: Test factory rejects invalid connector type
