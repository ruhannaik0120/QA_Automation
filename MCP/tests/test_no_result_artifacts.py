"""Prove database MCP execution remains stateless with respect to run evidence.

Result artifacts belong to the outer QA workflow, so the test executes through
a fake connector and verifies the MCP subsystem does not write report files.
"""

# region Imports and module setup
from config import Config
from services.query_service import QueryService
# endregion Imports and module setup


# region Class: Connector
class _Connector:
    """Return one deterministic query result without external infrastructure."""

    # region Function: Execute query
    def execute_query(self, query, *, database=None, timeout_seconds=None, max_rows=None):
        """Return a result in memory so filesystem side effects remain observable."""
        return {"columns": ["value"], "rows": [{"value": 1}], "rows_affected": 1}
    # endregion Function: Execute query
# endregion Class: Connector


# region Function: Test execution does not write result artifacts
def test_execution_does_not_write_result_artifacts(tmp_path, monkeypatch):
    """Verify execution does not write result artifacts."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_ACTIVE_PROFILE", "demo-local")
    Config.load()

    response = QueryService(_Connector()).execute_query(
        connection_profile="demo-local",
        sql="SELECT 1",
    ).to_dict()

    assert response["success"] is True
    assert list(tmp_path.rglob("*.json")) == []
# endregion Function: Test execution does not write result artifacts
