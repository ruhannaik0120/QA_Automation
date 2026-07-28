"""Verify MCP wrappers preserve argument forwarding and JSON response contracts.

Service doubles keep the suite at the transport boundary, proving wrappers add
no connector access, SQL behavior, or credential handling of their own.
"""

# region Imports and module setup
import tools.connection as connection_tools
import tools.metadata as metadata_tools
import tools.query as query_tools
# endregion Imports and module setup


# region Class: FakeResponse
class FakeResponse:
    """Provide the serializable response contract expected by tool wrappers."""

    # region Function: Init
    def __init__(self, payload):
        """Store the service payload that the wrapper must serialize."""
        self._payload = payload
    # endregion Function: Init

    # region Function: To dict
    def to_dict(self):
        """Return the payload through the production response interface."""
        return self._payload
    # endregion Function: To dict
# endregion Class: FakeResponse


# region Class: FakeService
class FakeService:
    """Capture wrapper arguments without invoking production services."""

    # region Function: Init
    def __init__(self):
        """Initialize ordered capture of all wrapper-to-service calls."""
        self.calls = []
    # endregion Function: Init

    # region Function: Test connection
    def test_connection(self, *args, **kwargs):
        """Capture connection arguments and return a valid tool response."""
        self.calls.append(("test_connection", args, kwargs))
        return FakeResponse(
            {
                "success": True,
                "tool": "test_connection",
                "environment": kwargs.get("environment", "DEV"),
                "request_id": "abc",
                "timestamp": "2026-06-28T00:00:00Z",
                "execution_time_ms": 1,
            }
        )
    # endregion Function: Test connection

    # region Function: Health
    def health(self, *args, **kwargs):
        """Capture health arguments and return deterministic status data."""
        self.calls.append(("health", args, kwargs))
        return FakeResponse(
            {
                "success": True,
                "tool": "health",
                "environment": kwargs.get("environment", "DEV"),
                "request_id": "abc",
                "timestamp": "2026-06-28T00:00:00Z",
                "execution_time_ms": 1,
                "status": "healthy",
            }
        )
    # endregion Function: Health

    # region Function: List databases
    def list_databases(self, *args, **kwargs):
        """Capture database-list arguments and return an empty inventory."""
        self.calls.append(("list_databases", args, kwargs))
        return FakeResponse(
            {
                "success": True,
                "tool": "list_databases",
                "environment": kwargs.get("environment", "DEV"),
                "request_id": "abc",
                "timestamp": "2026-06-28T00:00:00Z",
                "execution_time_ms": 1,
                "count": 0,
                "databases": [],
            }
        )
    # endregion Function: List databases

    # region Function: List tables
    def list_tables(self, *args, **kwargs):
        """Capture table-list arguments and return an empty inventory."""
        self.calls.append(("list_tables", args, kwargs))
        return FakeResponse({"success": True, "tool": "list_tables", "environment": kwargs.get("environment", "DEV"), "request_id": "abc", "timestamp": "2026-06-28T00:00:00Z", "execution_time_ms": 1, "count": 0, "tables": []})
    # endregion Function: List tables

    # region Function: Describe table
    def describe_table(self, *args, **kwargs):
        """Capture table-description arguments and return no columns."""
        self.calls.append(("describe_table", args, kwargs))
        return FakeResponse({"success": True, "tool": "describe_table", "environment": kwargs.get("environment", "DEV"), "request_id": "abc", "timestamp": "2026-06-28T00:00:00Z", "execution_time_ms": 1, "column_count": 0, "columns": []})
    # endregion Function: Describe table

    # region Function: Execute select query
    def execute_select_query(self, *args, **kwargs):
        """Capture deprecated alias arguments and return an empty result."""
        self.calls.append(("execute_select_query", args, kwargs))
        return FakeResponse({"success": True, "tool": "execute_select_query", "environment": kwargs.get("environment", "DEV"), "request_id": "abc", "timestamp": "2026-06-28T00:00:00Z", "execution_time_ms": 2, "rows": []})
    # endregion Function: Execute select query

    # region Function: Execute query
    def execute_query(self, *args, **kwargs):
        """Capture generic execution arguments and return an empty result."""
        self.calls.append(("execute_query", args, kwargs))
        return FakeResponse({"success": True, "tool": "execute_query", "environment": kwargs.get("environment", "DEV"), "request_id": "abc", "timestamp": "2026-06-28T00:00:00Z", "execution_time_ms": 2, "rows": []})
    # endregion Function: Execute query
# endregion Class: FakeService


# region Function: Test tool wrappers return structured payload
def test_tool_wrappers_return_structured_payload(monkeypatch):
    """Verify tool wrappers return structured payload."""
    fake_service = FakeService()
    monkeypatch.setattr(connection_tools, "query_service", fake_service)
    monkeypatch.setattr(metadata_tools, "query_service", fake_service)
    monkeypatch.setattr(query_tools, "query_service", fake_service)
    monkeypatch.setattr(
        query_tools,
        "bind_connection_profile_for_execution",
        lambda name, database=None: (
            fake_service,
            {"resolved_profile": name, "database": database},
        ),
    )

    test_payload = connection_tools.test_connection(environment="DEV")
    health_payload = connection_tools.health(environment="DEV")
    databases_payload = metadata_tools.list_databases(environment="DEV")
    tables_payload = metadata_tools.list_tables(database="sales", schema="dbo", environment="DEV")
    describe_payload = metadata_tools.describe_table(database="sales", table="orders", schema="dbo", environment="DEV")
    query_payload = query_tools.execute_query(
        connection_profile="sqlserver-sandbox",
        sql="UPDATE items SET active = 1",
        database="sales",
        environment="DEV",
    )
    alias_payload = query_tools.execute_select_query(
        connection_profile="sqlserver-sandbox",
        sql="SELECT 1",
        database="sales",
        environment="DEV",
    )

    assert test_payload["tool"] == "test_connection"
    assert health_payload["status"] == "healthy"
    assert databases_payload["tool"] == "list_databases"
    assert tables_payload["tool"] == "list_tables"
    assert describe_payload["tool"] == "describe_table"
    assert query_payload["execution_time_ms"] == 2
    assert alias_payload["tool"] == "execute_select_query"
# endregion Function: Test tool wrappers return structured payload


# region Function: Test query tools do not expose execution mode
def test_query_tools_do_not_expose_execution_mode():
    """Verify query tools do not expose execution mode."""
    import inspect

    assert "execution_mode" not in inspect.signature(query_tools.execute_query).parameters
    assert "execution_mode" not in inspect.signature(query_tools.execute_select_query).parameters
    assert inspect.signature(query_tools.execute_query).parameters["connection_profile"].default is inspect.Parameter.empty
    assert inspect.signature(query_tools.execute_select_query).parameters["connection_profile"].default is inspect.Parameter.empty
# endregion Function: Test query tools do not expose execution mode


# region Function: Test server query tools do not expose execution mode
def test_server_query_tools_do_not_expose_execution_mode():
    """Verify server query tools do not expose execution mode."""
    import ast
    from pathlib import Path

    server_tree = ast.parse((Path(__file__).parents[1] / "server.py").read_text(encoding="utf-8"))
    functions = {
        node.name: [argument.arg for argument in node.args.args]
        for node in server_tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "execution_mode" not in functions["tool_execute_query"]
    assert "execution_mode" not in functions["tool_execute_select_query"]
    assert functions["tool_execute_query"][0] == "connection_profile"
    assert functions["tool_execute_select_query"][0] == "connection_profile"
# endregion Function: Test server query tools do not expose execution mode
