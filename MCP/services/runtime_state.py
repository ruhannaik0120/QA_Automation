"""Hold process identity and the lock protecting mutable MCP runtime state.

Profile settings and cached connectors are process-wide. The shared re-entrant
lock prevents requests from observing a partially completed profile switch,
while the non-secret runtime ID supports diagnostics and log correlation.
"""

# region Imports and module setup
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4


# The active profile, Config class, and cached connector are process-wide state.
# Serializing MCP operations prevents a query from observing a half-finished
# profile switch or using a connector with another profile's credentials.
runtime_lock = RLock()
runtime_id = uuid4().hex[:12]
runtime_started_at = datetime.now(timezone.utc).isoformat()
# endregion Imports and module setup


# region Function: Runtime metadata
def runtime_metadata() -> dict[str, str]:
    """Return non-secret identity metadata for this process-isolated session."""

    return {
        "runtime_id": runtime_id,
        "runtime_started_at": runtime_started_at,
        "session_isolation": "one_client_per_process",
    }
# endregion Function: Runtime metadata
