"""Metadata-oriented MCP tools for the MCP server.

These wrappers expose database discovery capabilities while leaving all
connector communication and response shaping to the service layer.
"""

# region Imports and module setup
from services import query_service
from services.runtime_state import runtime_lock
# endregion Imports and module setup


# region Function: List databases
def list_databases(environment: str = "", timeout_seconds: int | None = None) -> dict:
    """Return all databases for the selected connector."""

    with runtime_lock:
        return query_service.list_databases(environment=environment, timeout_seconds=timeout_seconds).to_dict()
# endregion Function: List databases


# region Function: List tables
def list_tables(
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> dict:
    """Return the tables for a database, optionally filtered by schema."""

    with runtime_lock:
        return query_service.list_tables(
            database=database,
            schema=schema,
            environment=environment,
            timeout_seconds=timeout_seconds,
        ).to_dict()
# endregion Function: List tables


# region Function: Describe table
def describe_table(
    database: str = "",
    table: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
) -> dict:
    """Return normalized metadata for one explicit database object.

    The runtime lock keeps metadata discovery consistent with the active
    profile while ``QueryService`` owns validation and safe error shaping.
    """

    with runtime_lock:
        return query_service.describe_table(
            database=database,
            table=table,
            schema=schema,
            environment=environment,
            timeout_seconds=timeout_seconds,
        ).to_dict()
# endregion Function: Describe table


# region Function: Suggest columns
def suggest_columns(
    table: str,
    missing_column: str,
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    limit: int = 5,
) -> dict:
    """Suggest similar metadata column names without changing SQL."""

    with runtime_lock:
        return query_service.suggest_columns(
            table=table,
            missing_column=missing_column,
            database=database,
            schema=schema,
            environment=environment,
            timeout_seconds=timeout_seconds,
            limit=limit,
        ).to_dict()
# endregion Function: Suggest columns
