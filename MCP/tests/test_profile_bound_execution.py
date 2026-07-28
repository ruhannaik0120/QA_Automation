"""Verify deterministic profile binding for every database execution request.

The tests exercise the production tool, profile, and query-service layers with
offline connector doubles. They prove that execution does not depend on state
left by an earlier MCP call or runtime instance.
"""

# region Imports and module setup
import importlib
import json
from pathlib import Path

import pytest

from config import Config
from services import profile_service
from tools import query as query_tools

query_service_module = importlib.import_module("services.query_service")
# endregion Imports and module setup


# region Class: Profile aware connector
class ProfileAwareConnector:
    """Record connection tests and queries for the profile active at creation."""

    # region Function: Init
    def __init__(self, calls, *, fail_connection: bool = False):
        """Capture the selected non-secret target and shared call recorder."""

        self.calls = calls
        self.db_type = Config.DB_TYPE
        self.database = Config.DATABASE
        self.fail_connection = fail_connection
    # endregion Function: Init

    # region Function: Test connection
    def test_connection(self, database=None, timeout_seconds=None):
        """Return safe connection metadata or a controlled offline failure."""

        self.calls.append(("test_connection", self.db_type, database))
        if self.fail_connection:
            raise RuntimeError("offline connection validation failed")
        return {
            "connection_status": "connected",
            "connector_type": f"{self.db_type}-fake",
            "server_information": {"database": database},
        }
    # endregion Function: Test connection

    # region Function: Execute query
    def execute_query(self, statement, *, database=None, timeout_seconds=None, max_rows=None):
        """Record one statement and identify the connector that received it."""

        self.calls.append(("execute_query", self.db_type, database, statement))
        return {
            "columns": ["db_type", "database"],
            "rows": [[self.db_type, database]],
            "rows_affected": 1,
        }
    # endregion Function: Execute query

    # region Function: Close
    def close(self):
        """Record cache disposal without owning an external connection."""

        self.calls.append(("close", self.db_type, self.database))
    # endregion Function: Close
# endregion Class: Profile aware connector


# region Function: Profile runtime
@pytest.fixture
def profile_runtime(monkeypatch):
    """Install safe PostgreSQL and Snowflake profiles with offline connectors."""

    profiles = {
        "postgres-local": {
            "db_type": "postgresql",
            "host": "postgres.invalid",
            "database": "retail_qa",
            "username": "test-user",
            "password": "test-password",
        },
        "snowflake-personal": {
            "db_type": "snowflake",
            "host": "xy12345.ap-south-1",
            "database": "RETAIL_QA",
            "username": "test-user",
            "password": "test-password",
            "connection_options": {
                "warehouse": "TEST_WAREHOUSE",
                "schema": "PUBLIC",
                "role": "TEST_ROLE",
            },
        },
    }
    calls = []
    monkeypatch.setenv("DB_PROFILES_JSON", json.dumps(profiles))
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_ACTIVE_PROFILE", "default")
    monkeypatch.setattr(profile_service, "_active_profile", "default")
    monkeypatch.setattr(
        query_service_module.ConnectorFactory,
        "create",
        lambda selected_type=None: ProfileAwareConnector(calls),
    )
    query_service_module.reset_query_service()
    Config.load()

    yield calls

    query_service_module.reset_query_service()
# endregion Function: Profile runtime


# region Function: Test each call binds exact alternating profile
def test_each_call_binds_exact_alternating_profile(profile_runtime):
    """Alternate backends and prove each statement reaches its named profile."""

    postgres_first = query_tools.execute_query(
        connection_profile="postgres-local",
        database="retail_qa",
        sql="SELECT 1",
    )
    snowflake = query_tools.execute_query(
        connection_profile="snowflake-personal",
        database="RETAIL_QA",
        sql="SELECT 2",
    )
    postgres_second = query_tools.execute_query(
        connection_profile="postgres-local",
        database="retail_qa",
        sql="SELECT 3",
    )

    assert postgres_first["success"] is True
    assert postgres_first["resolved_profile"] == "postgres-local"
    assert postgres_first["metadata"]["db_type"] == "postgresql"
    assert postgres_first["rows"] == [["postgresql", "retail_qa"]]
    assert snowflake["success"] is True
    assert snowflake["resolved_profile"] == "snowflake-personal"
    assert snowflake["metadata"]["db_type"] == "snowflake"
    assert snowflake["metadata"]["schema"] == "PUBLIC"
    assert snowflake["metadata"]["role"] == "TEST_ROLE"
    assert snowflake["rows"] == [["snowflake", "RETAIL_QA"]]
    assert postgres_second["success"] is True
    assert postgres_second["resolved_profile"] == "postgres-local"
    assert postgres_second["rows"] == [["postgresql", "retail_qa"]]

    executions = [call for call in profile_runtime if call[0] == "execute_query"]
    assert executions == [
        ("execute_query", "postgresql", "retail_qa", "SELECT 1"),
        ("execute_query", "snowflake", "RETAIL_QA", "SELECT 2"),
        ("execute_query", "postgresql", "retail_qa", "SELECT 3"),
    ]
# endregion Function: Test each call binds exact alternating profile


# region Function: Test explicit profile survives runtime reset
def test_explicit_profile_survives_runtime_reset(profile_runtime, monkeypatch):
    """Simulate a restarted MCP runtime and bind the requested target anew."""

    first = query_tools.execute_query(
        connection_profile="postgres-local",
        database="retail_qa",
        sql="SELECT 1",
    )
    assert first["success"] is True

    query_service_module.reset_query_service()
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_ACTIVE_PROFILE", "default")
    monkeypatch.setattr(profile_service, "_active_profile", "default")
    Config.load()

    after_restart = query_tools.execute_query(
        connection_profile="snowflake-personal",
        database="RETAIL_QA",
        sql="SELECT 2",
    )

    assert after_restart["success"] is True
    assert after_restart["requested_profile"] == "snowflake-personal"
    assert after_restart["resolved_profile"] == "snowflake-personal"
    assert after_restart["metadata"]["db_type"] == "snowflake"
    assert after_restart["database"] == "RETAIL_QA"
# endregion Function: Test explicit profile survives runtime reset


# region Function: Test missing or unknown profile blocks execution
@pytest.mark.parametrize("profile_name", ["", "missing-profile"])
def test_missing_or_unknown_profile_blocks_execution(profile_runtime, profile_name):
    """Return structured blocked evidence without delegating ticket SQL."""

    response = query_tools.execute_query(
        connection_profile=profile_name,
        sql="SELECT 1",
    )

    assert response["success"] is False
    assert response["execution_status"] == "blocked"
    assert response["resolved_profile"] == ""
    assert [call for call in profile_runtime if call[0] == "execute_query"] == []
# endregion Function: Test missing or unknown profile blocks execution


# region Function: Test database mismatch blocks execution
def test_database_mismatch_blocks_execution(profile_runtime):
    """Reject a target that conflicts with the exact named profile."""

    response = query_tools.execute_query(
        connection_profile="postgres-local",
        database="another_database",
        sql="SELECT 1",
    )

    assert response["success"] is False
    assert response["execution_status"] == "blocked"
    assert "does not match" in response["error"]["detail"]
    assert [call for call in profile_runtime if call[0] == "execute_query"] == []
# endregion Function: Test database mismatch blocks execution


# region Function: Test failed connection validation blocks execution
def test_failed_connection_validation_blocks_execution(profile_runtime, monkeypatch):
    """Block before SQL when the named profile cannot pass its connection test."""

    monkeypatch.setattr(
        query_service_module.ConnectorFactory,
        "create",
        lambda selected_type=None: ProfileAwareConnector(profile_runtime, fail_connection=True),
    )

    response = query_tools.execute_query(
        connection_profile="postgres-local",
        database="retail_qa",
        sql="SELECT 1",
    )

    assert response["success"] is False
    assert response["execution_status"] == "blocked"
    assert "offline connection validation failed" in response["error"]["detail"]
    assert [call for call in profile_runtime if call[0] == "execute_query"] == []
# endregion Function: Test failed connection validation blocks execution


# region Function: Test profile credentials remain secret
def test_profile_credentials_remain_out_of_results_and_logs(profile_runtime, caplog, capsys):
    """Prove an environment-backed profile password never leaves the MCP runtime."""

    response = query_tools.execute_query(
        connection_profile="postgres-local",
        database="retail_qa",
        sql="SELECT 1",
    )
    captured = capsys.readouterr()
    observable_output = "\n".join(
        (str(response), caplog.text, captured.out, captured.err)
    )

    assert response["success"] is True
    assert "test-password" not in observable_output
# endregion Function: Test profile credentials remain secret


# region Function: Test execution path has no helper process launch
def test_execution_path_has_no_helper_or_process_launch():
    """Keep profile binding and SQL delegation inside the MCP server runtime."""

    mcp_root = Path(__file__).resolve().parents[1]
    production_paths = (
        mcp_root / "server.py",
        mcp_root / "services" / "profile_service.py",
        mcp_root / "services" / "query_service.py",
        mcp_root / "tools" / "query.py",
    )
    production_source = "\n".join(
        path.read_text(encoding="utf-8") for path in production_paths
    ).casefold()

    for forbidden in (
        "run_" "db_check",
        "subprocess",
        "popen",
        "os.system",
        "start-process",
        "python.exe",
    ):
        assert forbidden not in production_source
# endregion Function: Test execution path has no helper process launch
