"""Exercise SQL Server connector lifecycle and ODBC result normalization.

In-memory driver doubles verify connection ownership, row shaping, commits, and
cleanup without requiring an installed SQL Server or real credentials.
"""

# region Imports and module setup
from config import Config
from connectors.sqlserver.connector import SQLServerConnector


# These ODBC doubles verify connector behavior without a live SQL Server.
# endregion Imports and module setup

# region Class: FakeCursor
class FakeCursor:
    """Return deterministic metadata rows for connector assertions."""
    # region Function: Init
    def __init__(self):
        """Initialize one cursor with server metadata and query history."""
        self.description = [("server_name",), ("version",), ("logged_in_user",), ("utc_time",)]
        self._rows = [("server", "version", "user", "time")]
        self.executed = []
    # endregion Function: Init

    # region Function: Execute
    def execute(self, sql, *params):
        """Record the statement and bound parameters without executing SQL."""
        self.executed.append((sql, params))
    # endregion Function: Execute

    # region Function: Fetchone
    def fetchone(self):
        """Return the deterministic server-information row."""
        return self._rows[0]
    # endregion Function: Fetchone

    # region Function: Fetchall
    def fetchall(self):
        """Return all deterministic rows for result-shaping assertions."""
        return self._rows
    # endregion Function: Fetchall
# endregion Class: FakeCursor


# region Class: FakeConnection
class FakeConnection:
    """Track cursor access and closure for lifecycle assertions."""
    # region Function: Init
    def __init__(self):
        """Create an open connection with one reusable fake cursor."""
        self.cursor_obj = FakeCursor()
        self.closed = False
        self.autocommit = False
        self.timeout = 0
    # endregion Function: Init

    # region Function: Cursor
    def cursor(self):
        """Return the cursor owned by this fake connection."""
        return self.cursor_obj
    # endregion Function: Cursor

    # region Function: Close
    def close(self):
        """Record that connector cleanup closed the connection."""
        self.closed = True
    # endregion Function: Close
# endregion Class: FakeConnection


# region Class: FakeDriver
class FakeDriver:
    """Capture pyodbc arguments while returning an in-memory connection."""
    Error = RuntimeError
    version = "fake-odbc-1.0"

    # region Function: Init
    def __init__(self, connection=None):
        """Store the connection to return and initialize argument capture."""
        self.connection = connection or FakeConnection()
        self.captured = {}
    # endregion Function: Init

    # region Function: Connect
    def connect(self, conn_str, timeout=30):
        """Capture ODBC connection inputs and return the configured double."""
        self.captured = {"conn_str": conn_str, "timeout": timeout}
        return self.connection
    # endregion Function: Connect
# endregion Class: FakeDriver


# Establish one known profile so tests isolate only connector behavior.
# region Function: Configure generic settings
def _configure_generic_settings(monkeypatch):
    """Load a stable local SQL Server profile for connector-only tests."""
    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_DATABASE", "devdb")
    monkeypatch.setenv("DB_USERNAME", "")
    monkeypatch.setenv("DB_PASSWORD", "")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"driver": "ODBC Driver 18 for SQL Server"}')
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("DB_MAX_ROWS", "50")
    Config.load()
# endregion Function: Configure generic settings


# Context-managed operations must always close their ODBC connection.
# region Function: Test connection opens and closes
def test_connection_opens_and_closes(monkeypatch):
    """Verify connection opens and closes."""
    _configure_generic_settings(monkeypatch)
    sql_connector = SQLServerConnector()
    driver = FakeDriver()
    monkeypatch.setattr(sql_connector, "_driver", lambda: driver)
    connection = sql_connector.connect(database="devdb")

    assert isinstance(connection, FakeConnection)
    assert "SERVER={localhost}" in driver.captured["conn_str"]
    assert "DATABASE={devdb}" in driver.captured["conn_str"]
    assert "Trusted_Connection={yes}" in driver.captured["conn_str"]
    assert "Encrypt={no}" in driver.captured["conn_str"]
    assert "TrustServerCertificate={yes}" in driver.captured["conn_str"]
    assert driver.captured["timeout"] == 45
    assert connection.timeout == 45
# endregion Function: Test connection opens and closes


# Remote hosts receive secure encryption defaults unless explicitly overridden.
# region Function: Test remote sqlserver defaults to validated encryption
def test_remote_sqlserver_defaults_to_validated_encryption(monkeypatch):
    """Verify remote sqlserver defaults to validated encryption."""
    _configure_generic_settings(monkeypatch)
    monkeypatch.setenv("DB_HOST", "sql.company.internal")
    Config.load()
    sql_connector = SQLServerConnector()

    connection_string = sql_connector._connection_options(Config.connection_config())

    assert "Encrypt={yes}" in connection_string
    assert "TrustServerCertificate={no}" in connection_string
# endregion Function: Test remote sqlserver defaults to validated encryption


# A successful check returns useful metadata through the common connector shape.
# region Function: Test test connection returns server snapshot
def test_test_connection_returns_server_snapshot(monkeypatch):
    """Verify test connection returns server snapshot."""
    _configure_generic_settings(monkeypatch)
    fake_connection = FakeConnection()

    sql_connector = SQLServerConnector()
    monkeypatch.setattr(sql_connector, "_driver", lambda: FakeDriver(fake_connection))
    snapshot = sql_connector.test_connection(database="devdb")

    assert snapshot["connection_status"] == "connected"
    assert snapshot["db_type"] == "sqlserver"
    assert snapshot["server_information"]["server_name"] == "server"
    assert fake_connection.closed is True
# endregion Function: Test test connection returns server snapshot


# region Function: Test odbc values escape connection string delimiters
def test_odbc_values_escape_connection_string_delimiters(monkeypatch):
    """Verify odbc values escape connection string delimiters."""
    _configure_generic_settings(monkeypatch)
    monkeypatch.setenv("DB_USERNAME", "qa-user")
    monkeypatch.setenv("DB_PASSWORD", "p}ass;word")
    Config.load()
    connector = SQLServerConnector()

    connection_string = connector._build_connection_string(
        Config.connection_config(),
        "qa};SERVER=shadow",
    )

    assert "PWD={p}}ass;word}" in connection_string
    assert connection_string.endswith("DATABASE={qa}};SERVER=shadow};")
# endregion Function: Test odbc values escape connection string delimiters


# region Function: Test sqlserver rejects partial explicit credentials
def test_sqlserver_rejects_partial_explicit_credentials(monkeypatch):
    """Verify sqlserver rejects partial explicit credentials."""
    _configure_generic_settings(monkeypatch)
    monkeypatch.setenv("DB_USERNAME", "qa-user")
    monkeypatch.setenv("DB_PASSWORD", "")
    Config.load()

    connector = SQLServerConnector()

    import pytest

    with pytest.raises(Exception, match="must either both be set or both be empty"):
        connector._connection_options(Config.connection_config())
# endregion Function: Test sqlserver rejects partial explicit credentials
