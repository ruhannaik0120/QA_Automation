"""Exercise conservative SQL structure checks across supported dialects.

The cases cover comments, statement counts, row-limit forms, and write syntax;
validation is purely local and never executes the supplied SQL.
"""

# region Imports and module setup
from validation.sql_guard import validate_query
# endregion Imports and module setup


# region Function: Test validate query rejects sql comments
def test_validate_query_rejects_sql_comments():
    """Verify validate query rejects sql comments."""
    ok, reason = validate_query("SELECT 1 -- comment")
    assert ok is False
    assert "comments" in reason.lower()
# endregion Function: Test validate query rejects sql comments


# region Function: Test validate query allows select
def test_validate_query_allows_select():
    """Verify validate query allows select."""
    ok, reason = validate_query("SELECT name FROM sys.databases")
    assert ok is True
    assert reason == ""
# endregion Function: Test validate query allows select


# region Function: Test validator accepts approved write statement
def test_validator_accepts_approved_write_statement():
    """Verify validator accepts approved write statement."""
    ok, reason = validate_query("UPDATE users SET is_active = 1")
    assert ok is True
    assert reason == ""
# endregion Function: Test validator accepts approved write statement


# region Function: Test validate query rejects multiple statements
def test_validate_query_rejects_multiple_statements():
    """Verify validate query rejects multiple statements."""
    ok, reason = validate_query("UPDATE users SET is_active = 1; DELETE FROM users")
    assert ok is False
    assert "multiple statements" in reason.lower()
# endregion Function: Test validate query rejects multiple statements


# region Function: Test validate query allows cte
def test_validate_query_allows_cte():
    """Verify validate query allows cte."""
    ok, reason = validate_query("WITH cte AS (SELECT 1 AS value) SELECT * FROM cte")
    assert ok is True
    assert reason == ""
# endregion Function: Test validate query allows cte


# region Function: Test validate query allows comment tokens inside string literals
def test_validate_query_allows_comment_tokens_inside_string_literals():
    """Verify validate query allows comment tokens inside string literals."""
    ok, reason = validate_query("SELECT * FROM logs WHERE message = 'value--part'")
    assert ok is True
    assert reason == ""
# endregion Function: Test validate query allows comment tokens inside string literals


# region Function: Test validate query allows semicolon inside string literal
def test_validate_query_allows_semicolon_inside_string_literal():
    """Verify validate query allows semicolon inside string literal."""
    ok, reason = validate_query("SELECT 'alpha;beta' AS value")
    assert ok is True
    assert reason == ""
# endregion Function: Test validate query allows semicolon inside string literal


# region Function: Test sqlserver blocks write after select without semicolon
def test_sqlserver_blocks_write_after_select_without_semicolon():
    """Verify sqlserver blocks write after select without semicolon."""
    ok, reason = validate_query("SELECT 1\nDELETE FROM audit_log", "sqlserver")

    assert ok is False
    assert "multiple statements" in reason.lower()
# endregion Function: Test sqlserver blocks write after select without semicolon


# region Function: Test sqlserver quoted write word does not trigger batch guard
def test_sqlserver_quoted_write_word_does_not_trigger_batch_guard():
    """Verify sqlserver quoted write word does not trigger batch guard."""
    ok, reason = validate_query("SELECT [update] FROM audit_log", "sqlserver")

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver quoted write word does not trigger batch guard


# region Function: Test mysql hash comment is blocked
def test_mysql_hash_comment_is_blocked():
    """Verify mysql hash comment is blocked."""
    ok, reason = validate_query("SELECT 1 # hidden comment", "mysql")

    assert ok is False
    assert "comments" in reason.lower()
# endregion Function: Test mysql hash comment is blocked


# region Function: Test sqlserver blocks two write statements without semicolon
def test_sqlserver_blocks_two_write_statements_without_semicolon():
    """Verify sqlserver blocks two write statements without semicolon."""
    ok, reason = validate_query("UPDATE items SET active = 1\nDELETE FROM audit_log", "sqlserver")

    assert ok is False
    assert "multiple statements" in reason.lower()
# endregion Function: Test sqlserver blocks two write statements without semicolon


# region Function: Test sqlserver allows cte followed by its main update
def test_sqlserver_allows_cte_followed_by_its_main_update():
    """Verify sqlserver allows cte followed by its main update."""
    ok, reason = validate_query(
        "WITH target AS (SELECT id FROM items)\nUPDATE items SET active = 1 WHERE id IN (SELECT id FROM target)",
        "sqlserver",
    )

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver allows cte followed by its main update


# region Function: Test sqlserver allows union select on new line
def test_sqlserver_allows_union_select_on_new_line():
    """Verify sqlserver allows union select on new line."""
    ok, reason = validate_query("SELECT 1\nUNION ALL\nSELECT 2", "sqlserver")

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver allows union select on new line


# region Function: Test sqlserver blocks same line statement after write
def test_sqlserver_blocks_same_line_statement_after_write():
    """Verify sqlserver blocks same line statement after write."""
    for query in (
        "UPDATE items SET active = 1 DELETE FROM audit_log",
        "UPDATE items SET active = 1 SELECT 1",
    ):
        ok, reason = validate_query(query, "sqlserver")
        assert ok is False
        assert "multiple statements" in reason.lower()
# endregion Function: Test sqlserver blocks same line statement after write


# region Function: Test sqlserver allows multiline merge actions
def test_sqlserver_allows_multiline_merge_actions():
    """Verify sqlserver allows multiline merge actions."""
    query = """
        MERGE target AS t
        USING source AS s ON t.id = s.id
        WHEN MATCHED THEN UPDATE SET t.value = s.value
        WHEN NOT MATCHED THEN INSERT (id, value) VALUES (s.id, s.value)
        WHEN NOT MATCHED BY SOURCE THEN DELETE
    """

    ok, reason = validate_query(query, "sqlserver")

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver allows multiline merge actions


# region Function: Test sqlserver allows table hint with keyword
def test_sqlserver_allows_table_hint_with_keyword():
    """Verify sqlserver allows table hint with keyword."""
    ok, reason = validate_query("SELECT * FROM items WITH (NOLOCK)", "sqlserver")

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver allows table hint with keyword


# region Function: Test sqlserver blocks additional waitfor or set statement
def test_sqlserver_blocks_additional_waitfor_or_set_statement():
    """Verify sqlserver blocks additional waitfor or set statement."""
    for query in (
        "SELECT 1 WAITFOR DELAY '00:00:01'",
        "SELECT 1 SET NOCOUNT ON",
    ):
        ok, reason = validate_query(query, "sqlserver")
        assert ok is False
        assert "multiple statements" in reason.lower()
# endregion Function: Test sqlserver blocks additional waitfor or set statement


# region Function: Test sqlserver allows update set clause
def test_sqlserver_allows_update_set_clause():
    """Verify sqlserver allows update set clause."""
    ok, reason = validate_query("UPDATE items SET active = 1", "sqlserver")

    assert ok is True
    assert reason == ""
# endregion Function: Test sqlserver allows update set clause
