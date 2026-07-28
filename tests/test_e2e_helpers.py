"""Verify ticket initialization and report export helpers as one outer workflow.

Temporary ticket roots and generated evidence prove idempotent setup, redaction,
path safety, status computation, and supported report output without databases.
"""

# region Imports and module setup
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from modules import export_results, init_ticket_run
# endregion Imports and module setup


# region Function: Test ticket folder names are stable and collision resistant
def test_ticket_run_names_are_stable_and_collision_resistant():
    """Verify ticket run names are stable and collision resistant."""
    assert init_ticket_run.sanitize_ticket_key("abc-123") == "ABC-123"
    first = init_ticket_run.sanitize_ticket_key("ABC/123")
    second = init_ticket_run.sanitize_ticket_key("ABC?123")

    assert first != second
    assert first == export_results.sanitize_ticket_key("ABC/123")
    assert "/" not in first
    assert init_ticket_run.sanitize_ticket_key("CON.txt").startswith("RUN-")
# endregion Function: Test ticket folder names are stable and collision resistant


# region Function: Test initialize run is idempotent
def test_initialize_run_is_idempotent(tmp_path: Path):
    """Verify initialize run is idempotent."""
    ticket_runs_root = tmp_path / "ticket_runs"
    logs_root = tmp_path / "logs"
    run_folder, created = init_ticket_run.initialize_run("ABC-123", ticket_runs_root, logs_root)
    downloads_folder = run_folder / "downloads"
    assert list(downloads_folder.iterdir()) == []
    source_file = downloads_folder / "requirements.pdf"
    source_file.write_bytes(b"external source")
    marker = run_folder / "generated" / "qa_plan.md"
    marker.write_text("keep this", encoding="utf-8")

    _, created_again = init_ticket_run.initialize_run("ABC-123", ticket_runs_root, logs_root)

    assert len(created) == 6
    assert created_again == []
    assert marker.read_text(encoding="utf-8") == "keep this"
    assert source_file.read_bytes() == b"external source"
    payload = json.loads(
        (run_folder / "generated" / "execution_results" / "execution_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["schema_version"] == "1.0"
    assert downloads_folder.is_dir()
    assert (run_folder / "generated").is_dir()
    assert not (run_folder / "generated" / "input_selection.json").exists()
    assert (run_folder / "generated" / "generated_sql" / "generated_queries.sql").is_file()
    assert (run_folder / "generated" / "approvals" / "approval_log.md").is_file()
    assert (logs_root / "ABC-123.log").is_file()
    assert not (run_folder / "logs").exists()
    assert not (run_folder / "output").exists()
# endregion Function: Test initialize run is idempotent


# region Function: Test raw execution success is not a qa pass
def test_raw_execution_success_is_not_a_qa_pass():
    """Verify raw execution success is not a qa pass."""
    result = {"success": True, "request_id": "req-1", "rows": [{"defect_count": 2}]}

    assert export_results.query_status(result) == "executed_not_evaluated"
    summary = export_results.build_summary({}, [result], [])
    assert summary["status"] == "awaiting_evaluation"
    assert summary["passed"] == 0
    assert summary["not_evaluated"] == 1
# endregion Function: Test raw execution success is not a qa pass


# region Function: Test summary recomputes stale placeholder counts
def test_summary_recomputes_stale_placeholder_counts():
    """Verify summary recomputes stale placeholder counts."""
    payload = {
        "summary": {"status": "not_started", "total_queries": 0, "passed": 0},
        "query_results": [
            {"validation_status": "passed"},
            {"validation_status": "failed"},
        ],
    }

    summary = export_results.build_summary(payload, payload["query_results"], [])

    assert summary["status"] == "validation_failed"
    assert summary["total_queries"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
# endregion Function: Test summary recomputes stale placeholder counts


# region Function: Test empty or wrong ticket report is rejected
def test_empty_or_wrong_ticket_report_is_rejected():
    """Verify empty or wrong ticket report is rejected."""
    empty = {"ticket_id": "ABC-123", "query_results": [], "errors": []}
    with pytest.raises(ValueError, match="No execution results"):
        export_results.validate_report_payload("ABC-123", empty, require_results=True)

    wrong_ticket = {"ticket_id": "XYZ-999", "query_results": [{"success": True}]}
    with pytest.raises(ValueError, match="belongs to"):
        export_results.validate_report_payload("ABC-123", wrong_ticket, require_results=True)
# endregion Function: Test empty or wrong ticket report is rejected


# region Function: Test top level response list is normalized
def test_top_level_response_list_is_normalized(tmp_path: Path):
    """Verify top level response list is normalized."""
    path = tmp_path / "execution_result.json"
    path.write_text(json.dumps([{"success": True}, {"success": False}]), encoding="utf-8")

    payload = export_results.load_execution_result(path)

    assert len(payload["query_results"]) == 2
# endregion Function: Test top level response list is normalized


# region Function: Test sensitive values are redacted recursively
def test_sensitive_values_are_redacted_recursively():
    """Verify sensitive values are redacted recursively."""
    payload = {
        "auth": {"clientSecret": "hidden"},
        "connectionString": "Server=x;Password=hidden",
        "error": "Authorization: Bearer abc.def",
    }

    redacted = export_results.redact_sensitive(payload)

    assert redacted["auth"]["clientSecret"] == "[REDACTED]"
    assert redacted["connectionString"] == "[REDACTED]"
    assert "abc.def" not in redacted["error"]
# endregion Function: Test sensitive values are redacted recursively


# region Function: Test excel cells block formulas and invalid control characters
def test_excel_cells_block_formulas_and_invalid_control_characters():
    """Verify excel cells block formulas and invalid control characters."""
    assert export_results._excel_cell("=HYPERLINK(\"https://example.test\")").startswith("'=")
    assert export_results._excel_cell("unsafe\x00value") == "unsafevalue"
    assert len(export_results._excel_cell("x" * 40_000)) <= 32_767
# endregion Function: Test excel cells block formulas and invalid control characters


# region Function: Test html escapes values and reports profile
def test_html_escapes_values_and_reports_profile(tmp_path: Path):
    """Verify html escapes values and reports profile."""
    output = tmp_path / "report.html"
    payload = {
        "query_results": [
            {
                "check_id": "CHECK-1<script>",
                "validation_status": "passed",
                "metadata": {"profile": "qa-profile"},
                "row_count": 1,
                "rows_affected": 4,
                "rows": [{"value": "<unsafe>"}],
            }
        ]
    }

    export_results.export_html("ABC-123", payload, output)
    report = output.read_text(encoding="utf-8")

    assert "CHECK-1&lt;script&gt;" in report
    assert "&lt;unsafe&gt;" in report
    assert "qa-profile" in report
    assert "Rows Affected" in report
# endregion Function: Test html escapes values and reports profile


# region Function: Test excel export creates safe expected sheets
def test_excel_export_creates_safe_expected_sheets(tmp_path: Path):
    """Verify excel export creates safe expected sheets."""
    openpyxl = pytest.importorskip("openpyxl")
    workbook_class, font_class = export_results.load_openpyxl()
    output = tmp_path / "report.xlsx"
    payload = {
        "query_results": [
            {
                "check_id": "=UNSAFE()",
                "validation_status": "failed",
                "expected": "zero defects",
                "actual": "2 defects\x00",
                "rows": [{"defect_count": 2}],
            }
        ],
        "errors": [{"message": "+unsafe formula"}],
    }

    export_results.export_excel("ABC-123", payload, output, workbook_class, font_class)

    workbook = openpyxl.load_workbook(output, read_only=True, data_only=False)
    try:
        assert workbook.sheetnames == ["Summary", "Query Results", "Errors"]
        result_row = next(workbook["Query Results"].iter_rows(min_row=2, values_only=True))
        error_row = next(workbook["Errors"].iter_rows(min_row=2, values_only=True))
        assert result_row[1].startswith("'=")
        assert "\x00" not in result_row[5]
        assert error_row[3].startswith("'+")
    finally:
        workbook.close()
    assert not list(tmp_path.glob("*.tmp.xlsx"))
# endregion Function: Test excel export creates safe expected sheets


# region Function: Test cli initialization and both exports work end to end
def test_cli_initialization_and_both_exports_work_end_to_end(tmp_path: Path, monkeypatch, capsys):
    """Verify cli initialization and both exports work end to end."""
    pytest.importorskip("openpyxl")
    ticket_runs_root = tmp_path / "ticket_runs"
    logs_root = tmp_path / "logs"
    output_root = tmp_path / "output"
    monkeypatch.setattr(init_ticket_run, "TICKET_RUNS_ROOT", ticket_runs_root)
    monkeypatch.setattr(init_ticket_run, "LOGS_ROOT", logs_root)
    monkeypatch.setattr(sys, "argv", ["init_ticket_run.py", "ABC-123"])

    assert init_ticket_run.main() == 0

    result_path = (
        ticket_runs_root
        / "ABC-123"
        / "generated"
        / "execution_results"
        / "execution_result.json"
    )
    result_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "ticket_id": "ABC-123",
                "query_results": [
                    {
                        "check_id": "CHECK-1",
                        "execution_success": True,
                        "validation_status": "passed",
                        "expected": "one row",
                        "actual": "one row",
                        "rows": [{"value": 1}],
                    }
                ],
                "errors": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(export_results, "TICKET_RUNS_ROOT", ticket_runs_root)
    monkeypatch.setattr(export_results, "OUTPUT_ROOT", output_root)
    monkeypatch.setattr(sys, "argv", ["export_results.py", "ABC-123", "--format", "both"])

    assert export_results.main() == 0
    assert (output_root / "ABC-123" / "report.html").is_file()
    assert (output_root / "ABC-123" / "report.xlsx").is_file()
    assert not (ticket_runs_root / "ABC-123" / "output").exists()
    assert "report.xlsx" in capsys.readouterr().out
# endregion Function: Test cli initialization and both exports work end to end
