"""Verify every SQL dialect enforces the framework-wide result-row ceiling.

The suite inspects rewritten statements and bounded fetch behavior through
cursor doubles; no statement reaches a live database.
"""

# region Imports and module setup
from connectors.mysql.connector import MySQLConnector
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.snowflake.connector import SnowflakeConnector
from connectors.sqlserver.connector import SQLServerConnector
from connectors.base import unique_column_names


# LIMIT-based dialects must reduce explicit limits above the global ceiling.
# endregion Imports and module setup

# region Function: Test limit dialects clamp oversized explicit limit
def test_limit_dialects_clamp_oversized_explicit_limit():
    """Verify limit dialects clamp oversized explicit limit."""
    query = "SELECT * FROM items LIMIT 5000"

    assert MySQLConnector()._row_limit_sql(query, 100).endswith("LIMIT 100")
    assert PostgreSQLConnector()._row_limit_sql(query, 100).endswith("LIMIT 100")
    assert SnowflakeConnector()._row_limit_sql(query, 100).endswith("LIMIT 100")
# endregion Function: Test limit dialects clamp oversized explicit limit


# SQL Server's TOP syntax receives the same global ceiling guarantee.
# region Function: Test sqlserver clamps oversized top
def test_sqlserver_clamps_oversized_top():
    """Verify sqlserver clamps oversized top."""
    query = "SELECT TOP 5000 * FROM items"

    assert SQLServerConnector()._row_limit_sql(query, 100) == "SELECT TOP 100 * FROM items"
# endregion Function: Test sqlserver clamps oversized top


# Complex CTE text remains untouched and relies on the fetch-layer backstop.
# region Function: Test sqlserver cte relies on fetch cap without rewriting
def test_sqlserver_cte_relies_on_fetch_cap_without_rewriting():
    """Verify sqlserver cte relies on fetch cap without rewriting."""
    query = "WITH items AS (SELECT 1 AS value) SELECT * FROM items"

    assert SQLServerConnector()._row_limit_sql(query, 100) == query
# endregion Function: Test sqlserver cte relies on fetch cap without rewriting


# region Function: Test write statements are not modified by row limit logic
def test_write_statements_are_not_modified_by_row_limit_logic():
    """Verify write statements are not modified by row limit logic."""
    query = "UPDATE items SET active = 1"

    assert MySQLConnector()._row_limit_sql(query, 100) == query
    assert PostgreSQLConnector()._row_limit_sql(query, 100) == query
    assert SnowflakeConnector()._row_limit_sql(query, 100) == query
    assert SQLServerConnector()._row_limit_sql(query, 100) == query
# endregion Function: Test write statements are not modified by row limit logic


# Fetch limiting is the final defense when SQL cannot be safely rewritten.
# region Class: Cursor
class _Cursor:
    """Record the maximum number of rows requested from a driver cursor."""
    description = [("value",)]

    # region Function: Init
    def __init__(self):
        """Initialize fetch-size capture for the row-cap assertion."""
        self.fetchmany_size = None
    # endregion Function: Init

    # region Function: Fetchmany
    def fetchmany(self, size):
        """Record the bounded fetch request and return exactly that many rows."""
        self.fetchmany_size = size
        return [(number,) for number in range(size)]
    # endregion Function: Fetchmany
# endregion Class: Cursor


# The cursor fetch itself must never exceed the configured maximum.
# region Function: Test fetch layer enforces cap even when query cannot be rewritten
def test_fetch_layer_enforces_cap_even_when_query_cannot_be_rewritten():
    """Verify fetch layer enforces cap even when query cannot be rewritten."""
    cursor = _Cursor()

    payload = SQLServerConnector()._fetch_rows(cursor, max_rows=3)

    assert cursor.fetchmany_size == 3
    assert len(payload["rows"]) == 3
# endregion Function: Test fetch layer enforces cap even when query cannot be rewritten


# region Function: Test duplicate column names are preserved with stable suffixes
def test_duplicate_column_names_are_preserved_with_stable_suffixes():
    """Verify duplicate column names are preserved with stable suffixes."""
    assert unique_column_names(["id", "id", "name", "id"]) == ["id", "id_2", "name", "id_3"]
# endregion Function: Test duplicate column names are preserved with stable suffixes
