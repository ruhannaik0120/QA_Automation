"""Expose redacted runtime diagnostics through the thin MCP tool layer.

The wrapper acquires the runtime lock and delegates all data selection and
secret removal to ``QueryService``; it contains no configuration parsing.
"""

# region Imports and module setup
from services import query_service
from services.runtime_state import runtime_lock
# endregion Imports and module setup


# region Function: Config diagnostics
def config_diagnostics() -> dict:
    """Return a safe summary of the active runtime configuration."""

    with runtime_lock:
        return query_service.config_diagnostics().to_dict()
# endregion Function: Config diagnostics
