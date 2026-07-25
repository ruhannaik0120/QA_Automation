"""Verify deterministic metadata and query results from the offline connector.

These tests preserve a credential-free demonstration path and ensure the demo
backend follows the same normalized contract as real connectors.
"""

# region Imports and module setup
from connectors.demo.connector import DemoConnector
# endregion Imports and module setup


# region Function: Test demo connector lists sample databases
def test_demo_connector_lists_sample_databases():
    """Verify demo connector lists sample databases."""
    connector = DemoConnector()
    payload = connector.list_databases()

    assert payload["count"] >= 1
    assert payload["databases"][0]["name"] == "qa_demo"
# endregion Function: Test demo connector lists sample databases


# region Function: Test demo connector executes health check query
def test_demo_connector_executes_health_check_query():
    """Verify demo connector executes health check query."""
    connector = DemoConnector()
    payload = connector.execute_query("SELECT 1 AS health_check")

    assert payload["columns"] == ["health_check"]
    assert payload["rows"][0]["health_check"] == 1
# endregion Function: Test demo connector executes health check query


# region Function: Test demo connector describes sample table
def test_demo_connector_describes_sample_table():
    """Verify demo connector describes sample table."""
    connector = DemoConnector()
    payload = connector.describe_table(database="qa_demo", table="demo_items")

    assert payload["column_count"] == 3
    assert payload["columns"][0]["COLUMN_NAME"] == "item_id"
# endregion Function: Test demo connector describes sample table
