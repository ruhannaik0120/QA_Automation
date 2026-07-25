"""Expose profile discovery, switching, and reload operations to MCP clients.

These wrappers preserve the explicit confirmation contract enforced by the
profile service. They do not read environment files or manipulate connectors
directly.
"""

# region Imports and module setup
from services.profile_service import list_connection_profiles, reload_runtime_configuration, switch_connection_profile
# endregion Imports and module setup


# region Function: List profiles
def list_profiles() -> dict:
    """List profile names and readiness flags without returning secrets."""

    return list_connection_profiles()
# endregion Function: List profiles


# region Function: Switch profile
def switch_profile(name: str, confirm: bool = False) -> dict:
    """Switch profiles only after approval and always verify connectivity."""

    return switch_connection_profile(name, confirm=confirm, test_connection=True)
# endregion Function: Switch profile


# region Function: Reload config
def reload_config(confirm: bool = False) -> dict:
    """Atomically reload local configuration after explicit approval."""

    return reload_runtime_configuration(confirm=confirm)
# endregion Function: Reload config
