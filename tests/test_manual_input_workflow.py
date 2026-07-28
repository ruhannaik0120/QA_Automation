"""Protect the manual Jira-input selection, placement, and resume contract.

These tests exercise durable starter state and enforce the instruction-level
workflow without contacting Jira, repositories, or other network services.
"""

# region Imports and module setup
from __future__ import annotations

import json
from pathlib import Path

from modules import init_ticket_run


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASIC_INSTRUCTIONS_PATH = REPOSITORY_ROOT / "Basic_Instructions.md"
CONFIG_PATH = REPOSITORY_ROOT / "ticket_run_config.json"
WORKFLOW_PATH = REPOSITORY_ROOT / "skills" / "workflows" / "ruhan_poc_qaworkflow.md"
WORKFLOW_TEMPLATE_PATH = (
    REPOSITORY_ROOT / "skills" / "workflows" / "clientname_project_qaworkflow.md"
)
DOWNLOADER_PATH = REPOSITORY_ROOT / "modules" / "download_ticket_inputs.py"
EXPECTED_INPUT_ACQUISITION = {
    "mode_source": "selected_workflow",
    "default_mode": None,
    "supported_modes": ["manual", "automatic"],
    "workflow_must_declare_mode": True,
    "automatic_mode_requirements": [
        "explicit_workflow_permission",
        "required_acquisition_approvals_satisfied",
        "authentication_configured",
        "downloader_safety_controls_active",
    ],
}
# endregion Imports and module setup


# region Function: Load shared configuration
def _load_config() -> dict[str, object]:
    """Return the shared ticket-run configuration for contract assertions."""

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
# endregion Function: Load shared configuration


# region Function: Test neutral shared acquisition model
def test_shared_configuration_requires_workflow_defined_acquisition_mode():
    """Support manual and automatic modes without selecting a shared default."""

    config = _load_config()

    assert config["input_acquisition"] == EXPECTED_INPUT_ACQUISITION
    assert "input_selection" not in config["stable_artifact_paths"]
# endregion Function: Test neutral shared acquisition model


# region Function: Test neutral permanent instructions
def test_basic_instructions_are_acquisition_mode_neutral():
    """Keep POC selection and placement mechanics out of permanent instructions."""

    instructions = BASIC_INSTRUCTIONS_PATH.read_text(encoding="utf-8")

    assert "## Manual Input Acquisition" not in instructions
    assert "input_selection.json" not in instructions
    assert "proposed-input list" not in instructions
    assert "`include`, `exclude`, `defer`" not in instructions
    assert "this file does not choose manual or automatic acquisition" in instructions
    assert "Treat a hyperlink as a reference" in instructions
    assert "never invent missing or unreadable file contents" in instructions
# endregion Function: Test neutral permanent instructions


# region Function: Test POC manual mode declaration
def test_poc_workflow_alone_declares_manual_mode():
    """Confine tomorrow's manual acquisition decision to the POC workflow."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    template = WORKFLOW_TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "For this POC workflow only" in workflow
    assert "input_acquisition:\n  mode: manual" in workflow
    assert "mode: <manual-or-automatic>" in template
    assert "mode: manual" not in template
# endregion Function: Test POC manual mode declaration


# region Function: Test workflow input ordering
def test_jira_reference_discovery_precedes_selection_and_local_inspection():
    """Require Jira, selection, placement, verification, context, then planning."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    markers = (
        "Retrieve the authoritative Jira business request",
        "Discover, classify, and approve supporting input references",
        "Approve the proposed input selection.",
        "Manually place and verify approved local inputs",
        "Pause. Do not continue",
        "list every local file without opening file content or macros",
        "Synthesize the consolidated ticket context",
        "Approve context.",
        "Prepare the QA plan",
    )

    positions = [workflow.index(marker) for marker in markers]
    assert positions == sorted(positions)
# endregion Function: Test workflow input ordering


# region Function: Test proposed input decisions
def test_proposed_inputs_require_explicit_per_item_decisions():
    """Require complete proposed metadata and four explicit selection outcomes."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    for field in (
        "item number",
        "display name",
        "source type",
        "expected extension or content type",
        "source location",
        "relevance reason",
        "possible authentication requirement",
        "manual-download requirement",
    ):
        assert field in workflow
    for decision in ("`include`", "`exclude`", "`defer`", "`unclear / needs clarification`"):
        assert decision in workflow
    assert "`continue` counts only when this complete selection was already shown clearly" in workflow
# endregion Function: Test proposed input decisions


# region Function: Test manual placement blockers
def test_missing_and_unexpected_local_inputs_block_file_inspection():
    """Name missing files and require decisions for unexpected local files."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Stop and report each missing approved item" in workflow
    assert "For every unexpected file, ask whether it should be included before reading it" in workflow
    assert "Do not mark it verified merely because `input_selection.json` exists" in workflow
    assert "Do not read, acquire, or inspect excluded, deferred, unclear" in workflow
# endregion Function: Test manual placement blockers


# region Function: Test local document treatment
def test_word_excel_and_archives_are_local_untrusted_inputs_only():
    """Prevent remote document assumptions, macro opening, and archive extraction."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "inspect remote Word or Excel content" in workflow
    assert "Treat Word and Excel files as local inputs only" in workflow
    assert "Do not retrieve their remote versions automatically" in workflow
    assert "open macros, or extract archives" in workflow
    assert "Do not invent remote file contents, extracted Word or Excel content" in workflow
# endregion Function: Test local document treatment


# region Function: Test downloader remains inactive
def test_active_workflow_never_invokes_the_retained_downloader():
    """Keep downloader functionality available without granting the demo permission to call it."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    downloader = DOWNLOADER_PATH.read_text(encoding="utf-8")
    downloader_references = [
        line for line in workflow.splitlines() if "modules.download_ticket_inputs" in line
    ]

    assert "python -m modules.download_ticket_inputs" not in workflow
    assert downloader_references
    assert all("not invoke" in line.casefold() for line in downloader_references)
    assert "def download_direct_file(" in downloader
    assert "def download_github_package(" in downloader
    assert "def extract_github_package(" in downloader
    assert "def authentication_headers(" in downloader
    assert 'add_parser("file"' in downloader
    assert 'add_parser(\n        "github-package"' in downloader
# endregion Function: Test downloader remains inactive


# region Function: Test approval separation
def test_input_selection_and_context_approval_are_distinct_checkpoints():
    """Prevent input selection from authorizing interpretation or downstream planning."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    selection = workflow.index("Approve the proposed input selection.")
    context = workflow.index("Approve context.")
    planning = workflow.index("Prepare the QA plan")

    assert selection < context < planning
    assert "input-selection approval" in workflow
    assert "artifact existence as context approval" in workflow
# endregion Function: Test approval separation


# region Function: Test POC-created state and resume
def test_poc_created_input_state_and_local_documents_survive_resume(tmp_path: Path):
    """Preserve POC-owned selection state without making it a universal starter."""

    ticket_runs_root = tmp_path / "ticket_runs"
    logs_root = tmp_path / "logs"
    run_folder, _ = init_ticket_run.initialize_run("EXAMPLE-1", ticket_runs_root, logs_root)
    selection_path = run_folder / "generated" / "input_selection.json"
    assert not selection_path.exists()

    # The selected POC workflow, not the universal initializer, owns this state.
    selection = {
        "ticket_id": "EXAMPLE-1",
        "acquisition_mode": "manual",
        "discovery": {
            "status": "completed",
            "items": [
                {"item_number": 1, "display_name": "requirements.docx", "decision": "include"},
                {"item_number": 2, "display_name": "evidence.xlsx", "decision": "include"},
            ],
        },
        "selection_approval": {
            "status": "approved",
            "approved_by": "authorized-reviewer",
            "approved_on_utc": "2030-01-01T00:00:00+00:00",
        },
    }
    selection_path.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    downloads = run_folder / "downloads"
    (downloads / "requirements.docx").write_bytes(b"local-word-fixture")
    (downloads / "evidence.xlsx").write_bytes(b"local-excel-fixture")

    _, created_again = init_ticket_run.initialize_run("EXAMPLE-1", ticket_runs_root, logs_root)
    local_inventory = sorted(path.name for path in downloads.iterdir())
    resumed = json.loads(selection_path.read_text(encoding="utf-8"))

    assert created_again == []
    assert local_inventory == ["evidence.xlsx", "requirements.docx"]
    assert resumed == selection
# endregion Function: Test POC-created state and resume


# region Function: Test workflow template supports both modes
def test_workflow_template_supports_manual_and_automatic_acquisition():
    """Require an explicit mode while preserving the hardened automatic capability."""

    template = WORKFLOW_TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "mode: <manual-or-automatic>" in template
    assert "For `manual`" in template
    assert "For `automatic`" in template
    assert "allow `modules.download_ticket_inputs` only when" in template
    assert "all hardened downloader controls remain active" in template
# endregion Function: Test workflow template supports both modes
