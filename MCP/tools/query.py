"""Query-oriented MCP wrappers for approved database command execution.

The wrappers contain no SQL or driver logic. They forward MCP arguments to the
service layer and serialize its standard response contract.
"""

# region Imports and module setup
from services import query_service
from services.profile_service import bind_connection_profile_for_execution
from services.runtime_state import runtime_lock
# endregion Imports and module setup


# region Function: Execute query
def execute_query(
    connection_profile: str,
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
) -> dict:
    """Bind an exact approved profile and execute one approved SQL statement."""

    with runtime_lock:
        try:
            bound_service, binding = bind_connection_profile_for_execution(
                connection_profile,
                database=database,
            )
        except Exception as exc:
            return query_service.profile_binding_error(
                connection_profile=connection_profile,
                database=database,
                schema=schema,
                error=exc,
            ).to_dict()
        return bound_service.execute_query(
            connection_profile=binding["resolved_profile"],
            sql=sql,
            query=query,
            database=database,
            schema=schema,
            environment=environment,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
        ).to_dict()
# endregion Function: Execute query


# region Function: Execute select query
def execute_select_query(
    connection_profile: str,
    sql: str = "",
    query: str = "",
    database: str = "",
    schema: str = "",
    environment: str = "",
    timeout_seconds: int | None = None,
    max_rows: int | None = None,
) -> dict:
    """Deprecated compatibility alias for the generic execution tool."""

    with runtime_lock:
        try:
            bound_service, binding = bind_connection_profile_for_execution(
                connection_profile,
                database=database,
            )
        except Exception as exc:
            return query_service.profile_binding_error(
                connection_profile=connection_profile,
                database=database,
                schema=schema,
                error=exc,
                tool_name="execute_select_query",
            ).to_dict()
        return bound_service.execute_select_query(
            connection_profile=binding["resolved_profile"],
            sql=sql,
            query=query,
            database=database,
            schema=schema,
            environment=environment,
            timeout_seconds=timeout_seconds,
            max_rows=max_rows,
        ).to_dict()
# endregion Function: Execute select query
