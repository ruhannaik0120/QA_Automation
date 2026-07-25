"""Verify configuration loading, validation, and credential-safe diagnostics.

The suite mutates process environment only through pytest fixtures and confirms
invalid profiles fail before any connector or live database is contacted.
"""

# region Imports and module setup
import os

import pytest

import config as config_module

from config import Config, ConfigError
# endregion Imports and module setup


# region Function: Configure generic settings
def _configure_generic_settings(monkeypatch):
    """Install a valid baseline so each test isolates one configuration rule."""

    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_DATABASE", "devdb")
    monkeypatch.setenv("DB_USERNAME", "dev_user")
    monkeypatch.setenv("DB_PASSWORD", "dev_pass")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"driver": "ODBC Driver 18 for SQL Server"}')
    monkeypatch.setenv("DB_TIMEOUT_SECONDS", "20")
    monkeypatch.setenv("DB_MAX_ROWS", "100")
# endregion Function: Configure generic settings


# region Function: Test config validation passes with generic settings
def test_config_validation_passes_with_generic_settings(monkeypatch):
    """Verify config validation passes with generic settings."""
    _configure_generic_settings(monkeypatch)

    Config.load()
    Config.validate()

    profile = Config.connection_config()
    assert Config.DB_TYPE == "sqlserver"
    assert profile.db_type == "sqlserver"
    assert profile.host == "localhost"
    assert profile.database == "devdb"
    assert profile.connection_options == {"driver": "ODBC Driver 18 for SQL Server"}
# endregion Function: Test config validation passes with generic settings


# region Function: Test connection config has no execution mode
def test_connection_config_has_no_execution_mode(monkeypatch):
    """Verify connection config has no execution mode."""
    _configure_generic_settings(monkeypatch)

    Config.load()

    assert not hasattr(Config.connection_config(), "execution_mode")
# endregion Function: Test connection config has no execution mode


# region Function: Test config rejects non numeric max rows
def test_config_rejects_non_numeric_max_rows(monkeypatch):
    """Verify config rejects non numeric max rows."""
    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_MAX_ROWS", "abc")

    with pytest.raises(ConfigError, match="Expected an integer value"):
        Config.load()
# endregion Function: Test config rejects non numeric max rows


# region Function: Test invalid connection options raise structured error
def test_invalid_connection_options_raise_structured_error(monkeypatch):
    """Verify invalid connection options raise structured error."""
    monkeypatch.setenv("DB_TYPE", "sqlserver")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", "not-json")

    with pytest.raises(ConfigError, match="valid JSON"):
        Config.load()
# endregion Function: Test invalid connection options raise structured error


# region Function: Test config rejects unsupported db type
def test_config_rejects_unsupported_db_type(monkeypatch):
    """Verify config rejects unsupported db type."""
    monkeypatch.setenv("DB_TYPE", "oracle")
    monkeypatch.setenv("DB_HOST", "localhost")

    Config.load()

    with pytest.raises(ConfigError, match="DB_TYPE must be one of"):
        Config.validate()
# endregion Function: Test config rejects unsupported db type


# region Function: Test config allows demo without host
def test_config_allows_demo_without_host(monkeypatch):
    """Verify config allows demo without host."""
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_HOST", "")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")

    Config.load()
    Config.validate()

    assert Config.DB_TYPE == "demo"
# endregion Function: Test config allows demo without host


# region Function: Test sqlserver rejects partial credentials during startup validation
def test_sqlserver_rejects_partial_credentials_during_startup_validation(monkeypatch):
    """Verify sqlserver rejects partial credentials during startup validation."""
    _configure_generic_settings(monkeypatch)
    monkeypatch.setenv("DB_PASSWORD", "")

    Config.load()

    with pytest.raises(ConfigError, match="must either both be set or both be empty"):
        Config.validate()
# endregion Function: Test sqlserver rejects partial credentials during startup validation


# region Function: Test config rejects placeholder host
def test_config_rejects_placeholder_host(monkeypatch):
    """Verify config rejects placeholder host."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "<localhost>")

    Config.load()

    with pytest.raises(ConfigError, match="not a <placeholder>"):
        Config.validate()
# endregion Function: Test config rejects placeholder host


# region Function: Test config rejects quoted host
def test_config_rejects_quoted_host(monkeypatch):
    """Verify config rejects quoted host."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "'localhost'")

    Config.load()

    with pytest.raises(ConfigError, match="wrapping quotes"):
        Config.validate()
# endregion Function: Test config rejects quoted host


# region Function: Test config rejects invalid snowflake account
def test_config_rejects_invalid_snowflake_account(monkeypatch):
    """Verify config rejects invalid snowflake account."""
    monkeypatch.setenv("DB_TYPE", "snowflake")
    monkeypatch.setenv("DB_HOST", "https://org-account.snowflakecomputing.com")
    monkeypatch.setenv("DB_USERNAME", "user")

    Config.load()

    with pytest.raises(ConfigError, match="Snowflake"):
        Config.validate()
# endregion Function: Test config rejects invalid snowflake account


# region Function: Test config accepts snowflake locator with region segments
def test_config_accepts_snowflake_locator_with_region_segments(monkeypatch):
    """Verify config accepts snowflake locator with region segments."""
    monkeypatch.setenv("DB_TYPE", "snowflake")
    monkeypatch.setenv("DB_HOST", "xy12345.ap-south-1")
    monkeypatch.setenv("DB_USERNAME", "user")

    Config.load()

    assert Config.validate().HOST == "xy12345.ap-south-1"
# endregion Function: Test config accepts snowflake locator with region segments


# region Function: Test reload dotenv clears removed recognized values
def test_reload_dotenv_clears_removed_recognized_values(monkeypatch, tmp_path):
    """Verify reload dotenv clears removed recognized values."""
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("DB_TYPE=demo\nDB_DATABASE=qa_demo\n", encoding="utf-8")
    monkeypatch.setattr(config_module, "_DOTENV_PATH", dotenv_path)
    monkeypatch.setenv("DB_USERNAME", "stale-user")
    monkeypatch.setenv("DB_PASSWORD", "stale-password")

    Config.reload_dotenv(override=True)

    assert "DB_USERNAME" not in os.environ
    assert "DB_PASSWORD" not in os.environ
# endregion Function: Test reload dotenv clears removed recognized values


# region Function: Test config diagnostics redacts password
def test_config_diagnostics_redacts_password(monkeypatch):
    """Verify config diagnostics redacts password."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PASSWORD", "secret-value")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"port":5432,"password":"nested-secret"}')

    Config.load()
    diagnostics = Config.diagnostics()

    assert diagnostics["password_present"] is True
    assert "secret-value" not in str(diagnostics)
    assert diagnostics["connection_options"]["password"] == "[REDACTED]"
    assert "host" not in diagnostics
# endregion Function: Test config diagnostics redacts password


# region Function: Test diagnostics redact connection strings and private keys
def test_diagnostics_redact_connection_strings_and_private_keys(monkeypatch):
    """Verify diagnostics redact connection strings and private keys."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv(
        "DB_CONNECTION_OPTIONS",
        '{"connection_string":"Server=private","private_key":"key-material"}',
    )

    Config.load()
    diagnostics = Config.diagnostics()

    assert diagnostics["connection_options"]["connection_string"] == "[REDACTED]"
    assert diagnostics["connection_options"]["private_key"] == "[REDACTED]"
    assert "key-material" not in str(diagnostics)
# endregion Function: Test diagnostics redact connection strings and private keys


# region Function: Test diagnostics redact nested and variant secret keys
def test_diagnostics_redact_nested_and_variant_secret_keys(monkeypatch):
    """Verify diagnostics redact nested and variant secret keys."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv(
        "DB_CONNECTION_OPTIONS",
        '{"auth":{"clientSecret":"nested-value"},"sslpassword":"ssl-value","apiKey":"api-value"}',
    )

    Config.load()
    diagnostics = Config.diagnostics()

    assert diagnostics["connection_options"]["auth"]["clientSecret"] == "[REDACTED]"
    assert diagnostics["connection_options"]["sslpassword"] == "[REDACTED]"
    assert diagnostics["connection_options"]["apiKey"] == "[REDACTED]"
    assert "nested-value" not in str(diagnostics)
# endregion Function: Test diagnostics redact nested and variant secret keys


# region Function: Test config rejects connection options that override profile fields
@pytest.mark.parametrize("reserved_key", ["host", "SERVER", "user-id", "PWD", "database", "login_timeout"])
def test_config_rejects_connection_options_that_override_profile_fields(monkeypatch, reserved_key):
    """Verify config rejects connection options that override profile fields."""
    _configure_generic_settings(monkeypatch)
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"' + reserved_key + '":"shadow-target"}')

    Config.load()

    with pytest.raises(ConfigError, match="cannot override profile-controlled fields"):
        Config.validate()
# endregion Function: Test config rejects connection options that override profile fields


# region Function: Test error redaction handles nested secrets and bearer tokens
def test_error_redaction_handles_nested_secrets_and_bearer_tokens(monkeypatch):
    """Verify error redaction handles nested secrets and bearer tokens."""
    monkeypatch.setenv("DB_TYPE", "demo")
    monkeypatch.setenv("DB_DATABASE", "qa_demo")
    monkeypatch.setenv("DB_CONNECTION_OPTIONS", '{"auth":{"clientSecret":"nested-value"}}')
    Config.load()

    redacted = Config.redact_text("nested-value Authorization: Bearer abc.def")

    assert "nested-value" not in redacted
    assert "abc.def" not in redacted
# endregion Function: Test error redaction handles nested secrets and bearer tokens
