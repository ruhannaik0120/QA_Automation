"""MCP server entry point for the database connector runtime.

This file should only register MCP tools and start the server. It should not
contain business logic, SQL validation, or direct connector code.
"""

# region Imports and module setup
import json

from mcp.server.fastmcp import FastMCP

from config import Config
from logger import logger
from tools import (
    config_diagnostics,
    describe_table,
    execute_query,
    execute_select_query,
    health,
    list_databases,
    list_profiles,
    reload_config,
    list_tables,
    suggest_columns,
    switch_profile,
    test_connection,
)

Config.validate()
# FastMCP owns the protocol transport; this module only publishes our tool surface.
mcp = FastMCP("mcp-execution-framework")
logger.info("MCP Server initialising...")


# Profile tools expose safe profile metadata and approval-gated switching.
# endregion Imports and module setup

# region Function: Tool list connection profiles
@mcp.tool()
def tool_list_connection_profiles() -> str:
    """List configured connection profiles without exposing credentials."""

    return json.dumps(list_profiles(), indent=2, default=str)
# endregion Function: Tool list connection profiles


# region Function: Tool switch connection profile
@mcp.tool()
def tool_switch_connection_profile(name: str, confirm: bool = False) -> str:
    """Switch connectors after explicit approval and verify the new connection.

    First call with confirm=false to inspect the approval requirement. After the
    user approves the system transition, call with confirm=true.
    """

    # Tool errors are returned as JSON so an agent can explain failures without
    # exposing a Python traceback to the user.
    try:
        payload = switch_profile(name, confirm=confirm)
        return json.dumps({"success": True, "data": payload}, indent=2, default=str)
    except Exception as exc:
        return json.dumps({"success": False, "error": {"code": "PROFILE_SWITCH_FAILED", "message": Config.redact_text(exc)}}, indent=2)
# endregion Function: Tool switch connection profile


# region Function: Tool reload configuration
@mcp.tool()
def tool_reload_configuration(confirm: bool = False) -> str:
    """Reload local runtime configuration after explicit approval.

    Use this after updating the approved local .env file.
    Existing cached connectors are discarded so later tool calls use the new
    configuration snapshot.
    """

    try:
        payload = reload_config(confirm=confirm)
        return json.dumps({"success": True, "data": payload}, indent=2, default=str)
    except Exception as exc:
        return json.dumps({"success": False, "error": {"code": "CONFIG_RELOAD_FAILED", "message": Config.redact_text(exc)}}, indent=2)
# endregion Function: Tool reload configuration


# region Function: Tool config diagnostics
@mcp.tool()
def tool_config_diagnostics() -> str:
    """Return a safe summary of the active runtime configuration."""

    return json.dumps(config_diagnostics(), indent=2, default=str)
# endregion Function: Tool config diagnostics


# Connection and metadata tools let an agent inspect the active system without
# embedding any database-specific behavior in the MCP transport layer.
# region Function: Tool test connection
@mcp.tool()
def tool_test_connection(environment: str = "", database: str = "", timeout_seconds: int | None = None) -> str:
    """Verify database connectivity and return server metadata.

    Args:
        environment: Retained for compatibility; connector selection comes from DB_TYPE.
        database: Database used for the connection check.
        timeout_seconds: Optional command timeout override.

    Returns:
        JSON text containing the standard response envelope.
    """

    return json.dumps(test_connection(environment, database, timeout_seconds), indent=2, default=str)
# endregion Function: Tool test connection


# region Function: Tool health
@mcp.tool()
def tool_health(environment: str = "", timeout_seconds: int | None = None) -> str:
    """Return diagnostics for the selected database connector."""

    return json.dumps(health(environment, timeout_seconds), indent=2, default=str)
# endregion Function: Tool health


# region Function: Tool list databases
@mcp.tool()
def tool_list_databases(environment: str = "", timeout_seconds: int | None = None) -> str:
    """Serialize database discovery from the selected profile as MCP JSON.

    The service layer enforces environment and timeout rules; this registered
    wrapper performs no direct connector or credential access.
    """

    return json.dumps(list_databases(environment, timeout_seconds), indent=2, default=str)
# endregion Function: Tool list databases


# region Function: Tool list tables
@mcp.tool()
def tool_list_tables(
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> str:
    """List tables in a database, optionally filtered by schema."""

    return json.dumps(list_tables(database, schema, environment, timeout_seconds), indent=2, default=str)
# endregion Function: Tool list tables


# region Function: Tool describe table
@mcp.tool()
def tool_describe_table(
    database: str = "",
    table: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> str:
    """Serialize normalized metadata for one explicitly named table.

    Empty or invalid object identifiers are handled by the service and
    connector layers rather than inferred by the transport wrapper.
    """

    return json.dumps(describe_table(database, table, schema, environment, timeout_seconds), indent=2, default=str)
# endregion Function: Tool describe table


# region Function: Tool suggest columns
@mcp.tool()
def tool_suggest_columns(
    table: str,
    missing_column: str,
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    limit: int = 5,
) -> str:
    """Rank similar real columns without rewriting or executing SQL."""

    return json.dumps(
        suggest_columns(table, missing_column, database, schema, environment, timeout_seconds, limit),
        indent=2,
        default=str,
    )
# endregion Function: Tool suggest columns


# region Function: Tool execute query
@mcp.tool()
def tool_execute_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute approved SQL against the active profile's configured database.

    The compatibility schema argument is returned as request context only; SQL
    must qualify its own schema. Targeting another database requires an approved
    profile switch.
    """

    # The legacy select-named tool below remains available for existing clients.
    return json.dumps(
        execute_query(sql, query, database, schema, environment, timeout_seconds, max_rows),
        indent=2,
        default=str,
    )
# endregion Function: Tool execute query


# region Function: Tool execute select query
@mcp.tool()
def tool_execute_select_query(
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
) -> str:
    """Deprecated compatibility alias for tool_execute_query. Executes an approved SQL command/query using the active database profile."""

    return json.dumps(
        execute_select_query(sql, query, database, schema, environment, timeout_seconds, max_rows),
        indent=2,
        default=str,
    )
# endregion Function: Tool execute select query


# region Application entry point
if __name__ == "__main__":
    logger.info("MCP Server started. Waiting for connections...")
    mcp.run(transport="stdio")
# endregion Application entry point
