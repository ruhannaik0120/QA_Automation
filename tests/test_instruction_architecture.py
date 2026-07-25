"""Protect workflow routing, Agent Skill resolution, and instruction ownership.

These text-level tests keep permanent rules, workflow metadata, filenames, and
ticket-folder responsibilities synchronized without executing a workflow.
"""

# region Imports and module setup
from __future__ import annotations

import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPOSITORY_ROOT / "ticket_run_config.json"
CONTRACT_PATHS = (
    REPOSITORY_ROOT / "Basic_Instructions.md",
    REPOSITORY_ROOT / "docs" / "prd.md",
    REPOSITORY_ROOT / "docs" / "ADDING_AGENT_SKILLS.md",
    REPOSITORY_ROOT / "skills" / "workflows" / "clientname_project_qaworkflow.md",
    CONFIG_PATH,
)
EXPECTED_WORKFLOW_ROUTING = {
    "workflows_root": "skills/workflows",
    "workflow_template": "skills/workflows/clientname_project_qaworkflow.md",
    "workflow_filename_pattern": "<client-name>_<project-type>_qaworkflow.md",
    "workflow_variant_filename_pattern": (
        "<client-name>_<project-type>_<workflow-variant>_qaworkflow.md"
    ),
    "required_routing_fields": ["client_name", "project_type"],
    "optional_routing_fields": ["workflow_variant"],
    "active_workflow_document_type": "qa_workflow",
    "required_non_null_approval_fields": ["approved_by", "approved_on"],
    "agent_skills_root": "skills/agent_skills",
    "skill_instruction_filename": "SKILL.md",
}
RETIRED_REFERENCES = (
    "skills/QA_workflow_TEMPLATE.md",
    "QA_workflow_TEMPLATE.md",
    "skills/<clientname>_QA_workflow.md",
    "fallback.md",
    "client_key",
    "project_key",
    "workflow_variant_key",
    "workflow_key",
    "required_skills",
    "optional_skills",
    "skill_key",
)
# endregion Imports and module setup


# region Function: Load ticket-run configuration
def _load_config() -> dict[str, object]:
    """Load the shared ticket-run configuration as a JSON object."""

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
# endregion Function: Load ticket-run configuration


# region Function: Test finalized workflow-routing configuration
def test_workflow_routing_uses_finalized_contract():
    """Require the exact routing object and remove its obsolete duplicate contract."""

    config = _load_config()

    assert config["workflow_routing"] == EXPECTED_WORKFLOW_ROUTING
    assert "agent_skill_resolution" not in config
# endregion Function: Test finalized workflow-routing configuration


# region Function: Test configured instruction paths
def test_configured_instruction_paths_exist():
    """Ensure routing roots and the non-active workflow template exist."""

    routing = _load_config()["workflow_routing"]

    assert (REPOSITORY_ROOT / routing["workflows_root"]).is_dir()
    assert (REPOSITORY_ROOT / routing["workflow_template"]).is_file()
    assert (REPOSITORY_ROOT / routing["agent_skills_root"]).is_dir()
    assert routing["skill_instruction_filename"] == "SKILL.md"
# endregion Function: Test configured instruction paths


# region Function: Test retired routing references
def test_instruction_contract_has_no_retired_references():
    """Prevent superseded workflow and YAML-level skill fields from returning."""

    for path in CONTRACT_PATHS:
        content = path.read_text(encoding="utf-8")
        for retired_reference in RETIRED_REFERENCES:
            assert retired_reference not in content, (
                f"Retired reference {retired_reference!r} found in "
                f"{path.relative_to(REPOSITORY_ROOT)}"
            )
# endregion Function: Test retired routing references
