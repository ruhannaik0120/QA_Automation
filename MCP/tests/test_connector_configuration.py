"""Verify backend profiles map to exact driver connection arguments.

Fake MySQL, PostgreSQL, Snowflake, and SQL Server drivers capture arguments so
the tests can prove timeout, authentication, and option behavior offline.
"""

# region Imports and module setup
from contextlib import contextmanager

import pytest

from config import Config
from connectors.mysql.connector import MySQLConnector
from connectors.postgresql.connector import PostgreSQLConnector
from connectors.snowflake.connector import SnowflakeConnector


# Build profiles consistently so assertions focus on driver argument mapping.
# endregion Imports and module setup

# region Function: Configure
def _configure(monkeypatch, db_type: str, options: str = "{}") -> None:
    """Load one deterministic backend profile for argument-mapping tests."""
    monkeypatch.setenv("DB_TYPE", db_type)
    monkeypatch.setenv("DB_HOST", "db.example.test")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_USERNAME", "qa_user")
    monkeypatch.setenv("DB_PASSWORD", "qa_password")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", options)
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("DB_MAX_ROWS", "100")
    Config.load()
# endregion Function: Configure


# Each backend receives the expected driver keywords, defaults, and options.
# region Function: Test mysql connection arguments
def test_mysql_connection_arguments(monkeypatch):
    """Verify mysql connection arguments."""
    _configure(monkeypatch, "mysql", '{"port":3307,"ssl_disabled":true}')

    kwargs = MySQLConnector()._connection_kwargs(Config.connection_config(), "qa_demo")

    assert kwargs == {
        "host": "db.example.test",
        "port": 3307,
        "user": "qa_user",
        "password": "qa_password",
        "connection_timeout": 12,
        "read_timeout": 12,
        "write_timeout": 12,
        "database": "qa_demo",
        "ssl_disabled": True,
    }
# endregion Function: Test mysql connection arguments


# region Function: Test postgresql connection arguments
def test_postgresql_connection_arguments(monkeypatch):
    """Verify postgresql connection arguments."""
    _configure(monkeypatch, "postgresql", '{"port":5433,"sslmode":"require"}')

    kwargs = PostgreSQLConnector()._connection_kwargs(Config.connection_config(), "qa_demo")

    assert kwargs == {
        "host": "db.example.test",
        "port": 5433,
        "dbname": "qa_demo",
        "user": "qa_user",
        "password": "qa_password",
        "connect_timeout": 12,
        "options": "-c statement_timeout=12000",
        "sslmode": "require",
    }
# endregion Function: Test postgresql connection arguments


# region Function: Test snowflake connection arguments
def test_snowflake_connection_arguments(monkeypatch):
    """Verify snowflake connection arguments."""
    _configure(
        monkeypatch,
        "snowflake",
        '{"warehouse":"COMPUTE_WH","schema":"PUBLIC","role":"QA_ROLE"}',
    )

    kwargs = SnowflakeConnector()._connection_kwargs(Config.connection_config(), "QA_DEMO")

    assert kwargs == {
        "account": "db.example.test",
        "user": "qa_user",
        "password": "qa_password",
        "login_timeout": 12,
        "database": "QA_DEMO",
        "schema": "PUBLIC",
        "warehouse": "COMPUTE_WH",
        "role": "QA_ROLE",
    }
# endregion Function: Test snowflake connection arguments


# Transaction doubles prove commit behavior without touching live databases.
# region Class: WriteCursor
class _WriteCursor:
    """Represent a write cursor with a deterministic affected-row count."""
    description = None
    rowcount = 2

    # region Function: Execute
    def execute(self, query, *args, **kwargs):
        """Capture the accepted write and driver-specific execution options."""
        self.query = query
        self.execute_args = args
        self.execute_kwargs = kwargs
    # endregion Function: Execute

    # region Function: Close
    def close(self):
        """Provide the cursor cleanup hook expected by connectors."""
        return None
    # endregion Function: Close
# endregion Class: WriteCursor


# region Class: WriteConnection
class _WriteConnection:
    """Record whether a transactional connector commits an accepted write."""
    # region Function: Init
    def __init__(self):
        """Create an uncommitted transaction around one write cursor."""
        self.cursor_object = _WriteCursor()
        self.committed = False
    # endregion Function: Init

    # region Function: Cursor
    def cursor(self):
        """Return the transaction's deterministic write cursor."""
        return self.cursor_object
    # endregion Function: Cursor

    # region Function: Commit
    def commit(self):
        """Record the connector's successful transaction commit."""
        self.committed = True
    # endregion Function: Commit
# endregion Class: WriteConnection


# region Function: Test transactional connectors commit writes
@pytest.mark.parametrize(
    ("db_type", "connector_class"),
    [
        ("mysql", MySQLConnector),
        ("postgresql", PostgreSQLConnector),
        ("snowflake", SnowflakeConnector),
    ],
)
# MySQL, PostgreSQL, and Snowflake must commit successful write statements.
def test_transactional_connectors_commit_writes(monkeypatch, db_type, connector_class):
    """Verify transactional connectors commit writes."""
    _configure(monkeypatch, db_type)
    connector = connector_class()
    connection = _WriteConnection()

    # region Function: Fake connection
    @contextmanager
    def fake_connection(*args, **kwargs):
        """Yield the transaction double through the connector context API."""
        yield connection
    # endregion Function: Fake connection

    monkeypatch.setattr(connector, "_connection", fake_connection)

    result = connector.execute_query(
        "UPDATE demo_items SET status = 'verified'",
    )

    assert connection.committed is True
    assert result["rows_affected"] == 2
# endregion Function: Test transactional connectors commit writes


# region Function: Test postgresql commits write returning rows
def test_postgresql_commits_write_returning_rows(monkeypatch):
    """Verify postgresql commits write returning rows."""
    _configure(monkeypatch, "postgresql")
    connector = PostgreSQLConnector()
    connection = _WriteConnection()
    connection.cursor_object.description = [type("Column", (), {"name": "id"})()]
    connection.cursor_object.rowcount = 1
    connection.cursor_object.fetchmany = lambda size: [(1,)]

    # region Function: Fake connection
    @contextmanager
    def fake_connection(*args, **kwargs):
        """Yield the returning-write transaction through the context API."""
        yield connection
    # endregion Function: Fake connection

    monkeypatch.setattr(connector, "_connection", fake_connection)

    result = connector.execute_query("INSERT INTO items VALUES (1) RETURNING id")

    assert connection.committed is True
    assert result["rows"] == [{"id": 1}]
# endregion Function: Test postgresql commits write returning rows


# region Function: Test snowflake execute passes statement timeout
def test_snowflake_execute_passes_statement_timeout(monkeypatch):
    """Verify snowflake execute passes statement timeout."""
    _configure(monkeypatch, "snowflake")
    connector = SnowflakeConnector()
    cursor = _WriteCursor()

    connector._execute(cursor, "SELECT 1", timeout_seconds=7)

    assert cursor.query == "SELECT 1"
    assert cursor.execute_kwargs["timeout"] == 7
# endregion Function: Test snowflake execute passes statement timeout
