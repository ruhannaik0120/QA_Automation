"""Service-layer tests for delegation and response shaping."""

# region Imports and module setup
from config import Config
from models.errors import ErrorCode
from services.query_service import QueryService
# endregion Imports and module setup


# region Class: FakeConnector
class FakeConnector:
    """Record service delegation while returning deterministic connector data."""

    # region Function: Init
    def __init__(self):
        """Initialize this object."""
        self.calls = []
    # endregion Function: Init

    # region Function: Test connection
    def test_connection(self, database=None, timeout_seconds=None):
        """Verify connection."""
        self.calls.append(("test_connection", database, timeout_seconds))
        return {
            "connector_type": "FakeConnector",
            "connection_status": "connected",
            "server_information": {"server_name": "server", "version": "version-string"},
        }
    # endregion Function: Test connection

    # region Function: Health check
    def health_check(self, database=None, timeout_seconds=None):
        """Handle health check."""
        self.calls.append(("health_check", database, timeout_seconds))
        return {
            "connector_type": "FakeConnector",
            "connection_status": "connected",
            "server_information": {"server_name": "server", "version": "version-string"},
        }
    # endregion Function: Health check

    # region Function: List databases
    def list_databases(self, timeout_seconds=None):
        """Handle list databases."""
        self.calls.append(("list_databases", timeout_seconds))
        return {"count": 2, "databases": [{"name": "alpha"}, {"name": "beta"}]}
    # endregion Function: List databases

    # region Function: List tables
    def list_tables(self, database=None, schema=None, timeout_seconds=None):
        """Handle list tables."""
        self.calls.append(("list_tables", database, schema, timeout_seconds))
        return {"count": 1, "tables": [{"TABLE_SCHEMA": schema or "dbo", "TABLE_NAME": "items"}]}
    # endregion Function: List tables

    # region Function: Describe table
    def describe_table(self, database=None, table=None, schema=None, timeout_seconds=None):
        """Handle describe table."""
        self.calls.append(("describe_table", database, table, schema, timeout_seconds))
        return {
            "database": database,
            "schema": schema,
            "table": table,
            "column_count": 1,
            "columns": [{"COLUMN_NAME": "name", "DATA_TYPE": "nvarchar"}],
        }
    # endregion Function: Describe table

    # region Function: Execute query
    def execute_query(self, query, *, database=None, timeout_seconds=None, max_rows=None):
        """Handle execute query."""
        self.calls.append(("execute_query", query, database, timeout_seconds, max_rows))
        return {"columns": ["name"], "rows": [("alpha",), ("beta",)]}
    # endregion Function: Execute query

    # region Function: Close
    def close(self):
        """Handle close."""
        self.calls.append(("close",))
    # endregion Function: Close
# endregion Class: FakeConnector


# region Function: Configure settings
def _configure_settings(monkeypatch):
    """Set stable policy values without loading credentials or live drivers."""

    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_DATABASE", "sales")
    monkeypatch.setenv("DB_USERNAME", "dev_user")
    monkeypatch.setenv("DB_PASSWORD", "dev_pass")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"driver": "ODBC Driver 18 for SQL Server"}')
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("DB_MAX_ROWS", "25")
    monkeypatch.setenv("DB_ACTIVE_PROFILE", "sqlserver-sandbox")
    Config.load()
# endregion Function: Configure settings


# region Function: Test execute select query delegates to connector
def test_execute_select_query_delegates_to_connector(monkeypatch):
    """Verify execute select query delegates to connector."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_select_query(sql="SELECT name FROM sys.databases", environment="ignored").to_dict()

    assert response["success"] is True
    assert response["tool"] == "execute_select_query"
    assert response["environment"] == "SQLSERVER"
    assert response["row_count"] == 2
    assert response["metadata"]["row_limit"] == 25
    assert connector.calls[0][0] == "execute_query"
    assert connector.calls[0][1] == "SELECT name FROM sys.databases"
# endregion Function: Test execute select query delegates to connector


# region Function: Test health returns structured status
def test_health_returns_structured_status(monkeypatch):
    """Verify health returns structured status."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.health(environment="ignored").to_dict()

    assert response["success"] is True
    assert response["tool"] == "health"
    assert response["environment"] == "SQLSERVER"
    assert response["connection_status"] == "connected"
    assert response["server_information"]["server_name"] == "server"
    assert connector.calls[0][0] == "health_check"
# endregion Function: Test health returns structured status


# region Function: Test metadata calls delegate
def test_metadata_calls_delegate(monkeypatch):
    """Verify metadata calls delegate."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    databases = service.list_databases().to_dict()
    tables = service.list_tables(database="sales", schema="dbo").to_dict()
    details = service.describe_table(database="sales", table="items", schema="dbo").to_dict()

    assert databases["count"] == 2
    assert tables["count"] == 1
    assert details["column_count"] == 1
    assert [call[0] for call in connector.calls[:3]] == ["list_databases", "list_tables", "describe_table"]
# endregion Function: Test metadata calls delegate


# region Function: Test suggest columns uses metadata without executing sql
def test_suggest_columns_uses_metadata_without_executing_sql(monkeypatch):
    """Verify suggest columns uses metadata without executing sql."""
    _configure_settings(monkeypatch)

    # region Class: MetadataConnector
    class MetadataConnector(FakeConnector):
        # region Function: Describe table
        """Provide the MetadataConnector implementation."""
        def describe_table(self, database=None, table=None, schema=None, timeout_seconds=None):
            """Handle describe table."""
            self.calls.append(("describe_table", database, table, schema, timeout_seconds))
            return {
                "database": database,
                "schema": schema,
                "table": table,
                "columns": [
                    {"COLUMN_NAME": "order_id", "DATA_TYPE": "integer"},
                    {"COLUMN_NAME": "order_status", "DATA_TYPE": "varchar"},
                    {"COLUMN_NAME": "created_at", "DATA_TYPE": "timestamp"},
                ],
            }
        # endregion Function: Describe table
    # endregion Class: MetadataConnector

    connector = MetadataConnector()
    response = QueryService(connector).suggest_columns(
        table="orders",
        missing_column="status",
        database="sales",
        schema="dbo",
    ).to_dict()

    assert response["success"] is True
    assert response["suggestions"][0]["column"] == "order_status"
    assert response["sql_modified"] is False
    assert response["sql_executed"] is False
    assert response["approval_required_before_revised_sql"] is True
    assert [call[0] for call in connector.calls] == ["describe_table"]
# endregion Function: Test suggest columns uses metadata without executing sql


# region Function: Test suggest columns requires table and column
def test_suggest_columns_requires_table_and_column(monkeypatch):
    """Verify suggest columns requires table and column."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()

    response = QueryService(connector).suggest_columns(table="", missing_column="status").to_dict()

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.CONFIG_INVALID
    assert connector.calls == []
# endregion Function: Test suggest columns requires table and column


# region Function: Test response preserves reserved fields
def test_response_preserves_reserved_fields(monkeypatch):
    """Verify response preserves reserved fields."""
    _configure_settings(monkeypatch)
    service = QueryService(FakeConnector())

    response = service._response(
        tool="execute_select_query",
        environment="SQLSERVER",
        success=True,
        request_id="req-1",
        start_time=0.0,
        data={"success": False, "request_id": "shadow", "tool": "shadow-tool", "environment": "shadow-env", "custom": "value"},
    ).to_dict()

    assert response["success"] is True
    assert response["request_id"] == "req-1"
    assert response["tool"] == "execute_select_query"
    assert response["environment"] == "SQLSERVER"
    assert response["data"]["success"] is False
    assert response["data"]["request_id"] == "shadow"
    assert response["custom"] == "value"
    assert response["metadata"]["session_isolation"] == "one_client_per_process"
    assert response["metadata"]["runtime_id"]
# endregion Function: Test response preserves reserved fields


# region Function: Test execute query executes approved write statement
def test_execute_query_executes_approved_write_statement(monkeypatch):
    """Verify execute query executes approved write statement."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_query(sql="DELETE FROM items", environment="ignored").to_dict()

    assert response["success"] is True
    assert response["tool"] == "execute_query"
    assert response["query"] == "DELETE FROM items"
    assert connector.calls[0][1] == "DELETE FROM items"
# endregion Function: Test execute query executes approved write statement


# region Function: Test execute query falls back from whitespace sql
def test_execute_query_falls_back_from_whitespace_sql(monkeypatch):
    """Use the normalized query when the sql compatibility argument is blank."""

    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_query(sql="   ", query="  SELECT 1  ").to_dict()

    assert response["success"] is True
    assert response["query"] == "SELECT 1"
    assert connector.calls == [("execute_query", "SELECT 1", "sales", 20, 25)]
# endregion Function: Test execute query falls back from whitespace sql


# region Function: Test execute query rejects blank statements
def test_execute_query_rejects_blank_statements(monkeypatch):
    """Preserve the empty-statement error for blank and whitespace-only inputs."""

    _configure_settings(monkeypatch)
    for sql, query in (("", ""), ("   ", "\t")):
        connector = FakeConnector()
        service = QueryService(connector)

        response = service.execute_query(sql=sql, query=query).to_dict()

        assert response["success"] is False
        assert response["error"]["code"] == ErrorCode.QUERY_BLOCKED
        assert response["error"]["message"] == "Empty query is not allowed."
        assert connector.calls == []
# endregion Function: Test execute query rejects blank statements


# region Function: Test execute query rejects conflicting sql arguments
def test_execute_query_rejects_conflicting_sql_arguments(monkeypatch):
    """Verify execute query rejects conflicting sql arguments."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_query(sql="SELECT 1", query="DELETE FROM items").to_dict()

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.CONFIG_INVALID
    assert connector.calls == []
# endregion Function: Test execute query rejects conflicting sql arguments


# region Function: Test execute query accepts identical normalized statements
def test_execute_query_accepts_identical_normalized_statements(monkeypatch):
    """Execute one normalized statement when both compatibility inputs agree."""

    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_query(sql="  SELECT 1  ", query="\nSELECT 1\t").to_dict()

    assert response["success"] is True
    assert response["query"] == "SELECT 1"
    assert connector.calls == [("execute_query", "SELECT 1", "sales", 20, 25)]
# endregion Function: Test execute query accepts identical normalized statements


# region Function: Test execute query rejects database outside active profile
def test_execute_query_rejects_database_outside_active_profile(monkeypatch):
    """Verify execute query rejects database outside active profile."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_query(sql="SELECT 1", database="another_database").to_dict()

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.CONFIG_INVALID
    assert "profile switch" in response["error"]["detail"]
    assert connector.calls == []
# endregion Function: Test execute query rejects database outside active profile


# region Function: Test deprecated alias uses same generic execution path
def test_deprecated_alias_uses_same_generic_execution_path(monkeypatch):
    """Verify deprecated alias uses same generic execution path."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_select_query(sql="UPDATE items SET active = 1").to_dict()

    assert response["success"] is True
    assert response["tool"] == "execute_select_query"
    assert connector.calls[0][0] == "execute_query"
# endregion Function: Test deprecated alias uses same generic execution path


# region Function: Test request row limit cannot exceed configured cap
def test_request_row_limit_cannot_exceed_configured_cap(monkeypatch):
    """Verify request row limit cannot exceed configured cap."""
    _configure_settings(monkeypatch)
    connector = FakeConnector()
    service = QueryService(connector)

    response = service.execute_select_query(sql="SELECT name FROM items", max_rows=10_000).to_dict()

    assert response["success"] is True
    assert response["metadata"]["row_limit"] == 25
    assert response["metadata"]["profile"] == "sqlserver-sandbox"
    assert connector.calls[0][4] == 25
# endregion Function: Test request row limit cannot exceed configured cap


# region Function: Test non positive row limit is rejected
def test_non_positive_row_limit_is_rejected(monkeypatch):
    """Verify non positive row limit is rejected."""
    _configure_settings(monkeypatch)
    service = QueryService(FakeConnector())

    response = service.execute_select_query(sql="SELECT 1", max_rows=0).to_dict()

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.CONFIG_INVALID
# endregion Function: Test non positive row limit is rejected


# region Function: Test non positive timeout is rejected
def test_non_positive_timeout_is_rejected(monkeypatch):
    """Verify non positive timeout is rejected."""
    _configure_settings(monkeypatch)
    service = QueryService(FakeConnector())

    response = service.health(timeout_seconds=-1).to_dict()

    assert response["success"] is False
    assert response["error"]["code"] == ErrorCode.CONFIG_INVALID
# endregion Function: Test non positive timeout is rejected


# region Function: Test connector errors redact configured password
def test_connector_errors_redact_configured_password(monkeypatch):
    """Verify connector errors redact configured password."""
    _configure_settings(monkeypatch)

    # region Class: FailingConnector
    class FailingConnector(FakeConnector):
        # region Function: Execute query
        """Provide the FailingConnector implementation."""
        def execute_query(self, query, **kwargs):
            """Handle execute query."""
            raise RuntimeError("Authentication failed for password dev_pass")
        # endregion Function: Execute query
    # endregion Class: FailingConnector

    response = QueryService(FailingConnector()).execute_query(sql="SELECT 1").to_dict()

    assert response["success"] is False
    assert "dev_pass" not in str(response)
    assert "[REDACTED]" in response["error"]["detail"]
# endregion Function: Test connector errors redact configured password
