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
COPILOT_INSTRUCTIONS_PATH = REPOSITORY_ROOT / ".github" / "copilot-instructions.md"
PORTABLE_BOOTSTRAP_PATH = REPOSITORY_ROOT / "docs" / "PORTABLE_AI_CLIENT_BOOTSTRAP.md"
POC_WORKFLOW_RELATIVE_PATH = "skills/workflows/ruhan_poc_qaworkflow.md"
POC_WORKFLOW_PATH = REPOSITORY_ROOT / POC_WORKFLOW_RELATIVE_PATH
WORKFLOW_TEMPLATE_PATH = REPOSITORY_ROOT / "skills" / "workflows" / "clientname_project_qaworkflow.md"
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
    "approval_metadata_exempt_workflows": [POC_WORKFLOW_RELATIVE_PATH],
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


# region Function: Test narrow POC approval-metadata exemption
def test_poc_approval_metadata_exemption_is_narrow_and_valid():
    """Allow null approval metadata only for the exact configured POC workflow."""

    routing = _load_config()["workflow_routing"]
    exempt_workflows = routing["approval_metadata_exempt_workflows"]

    assert exempt_workflows == [POC_WORKFLOW_RELATIVE_PATH]
    assert POC_WORKFLOW_PATH.is_file()

    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")
    frontmatter = workflow.split("---", 2)[1]
    assert 'document_type: "qa_workflow"' in frontmatter
    assert "approved_by: null" in frontmatter
    assert "approved_on: null" in frontmatter
# endregion Function: Test narrow POC approval-metadata exemption


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


# region Function: Test thin Copilot adapter
def test_copilot_adapter_is_thin_and_points_to_basic_instructions():
    """Keep Copilot discovery portable and subordinate to shared instructions."""

    content = COPILOT_INSTRUCTIONS_PATH.read_text(encoding="utf-8")

    assert "Basic_Instructions.md" in content
    assert "authoritative" in content
    assert len(content.splitlines()) < 20
    assert PORTABLE_BOOTSTRAP_PATH.is_file()
# endregion Function: Test thin Copilot adapter


# region Function: Test preflight ordering
def test_ai_preflight_precedes_workspace_initialization():
    """Declare AI preflight before workflow routing and ticket initialization."""

    instructions = (REPOSITORY_ROOT / "Basic_Instructions.md").read_text(encoding="utf-8")
    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow enforcement performed by the AI client, not a Python preflight module" in instructions
    assert instructions.index("## AI-Orchestrated Preflight") < instructions.index(
        "## Selecting A Client Workflow"
    )
    assert "global_preflight_succeeded" in workflow
    assert workflow.index("global_preflight_succeeded") < workflow.index(
        "Run the existing initializer behavior"
    )
# endregion Function: Test preflight ordering


# region Function: Test direct Jira retrieval contract
def test_direct_jira_retrieval_reuses_authorized_cloud_identifier():
    """Require direct Jira access and reuse of the resolved site identifier."""

    instructions = (REPOSITORY_ROOT / "Basic_Instructions.md").read_text(encoding="utf-8")
    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "retrieve the exact issue directly" in instructions
    assert "reuse that resolved Jira identifier" in instructions
    assert "Broad Atlassian search does not replace direct issue retrieval" in instructions
    assert "same identifier" in workflow
# endregion Function: Test direct Jira retrieval contract


# region Function: Test database profile sequence
def test_database_profile_discovery_precedes_execution_approval():
    """Discover profile mappings before approval and switch only afterward."""

    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")
    discovery = workflow.index("List database profiles through secret-safe MCP discovery")
    approval = workflow.index("Approve the proposed read-only execution scope. No DDL or DML.")
    switch = workflow.index("Switch only to a profile and target included")
    connection = workflow.index("Validate the connection after switching")

    assert discovery < approval < switch < connection
# endregion Function: Test database profile sequence


# region Function: Test genuine approval checkpoints
def test_only_context_execution_and_write_approvals_remain():
    """Keep normal read-only prompts compact and operational failures blocking."""

    config = _load_config()
    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert [item["id"] for item in config["human_approval_checkpoints"]] == [
        "ticket_context_complete",
        "database_execution",
        "write_operation",
    ]
    assert workflow.count("**Human approval required:** `true`") == 2
    assert "Approve context." in workflow
    assert "Approve the proposed read-only execution scope. No DDL or DML." in workflow
    assert "failures are blockers rather than approval checkpoints" in workflow
# endregion Function: Test genuine approval checkpoints


# region Function: Test runtime and resume boundaries
def test_runtime_writes_and_resume_evidence_are_ticket_scoped():
    """Preserve runtime-only writes and artifact-derived chat recovery."""

    instructions = (REPOSITORY_ROOT / "Basic_Instructions.md").read_text(encoding="utf-8")

    for expected_path in (
        "ticket_runs/<ticket-id>/**",
        "logs/<ticket-id>.log",
        "output/<ticket-id>/**",
    ):
        assert expected_path in instructions
    for artifact in (
        "routing configuration",
        "ticket context",
        "source manifests",
        "approval logs",
        "QA plan",
        "generated SQL",
        "execution results",
        "workflow log",
    ):
        assert artifact in instructions
# endregion Function: Test runtime and resume boundaries


# region Function: Test reusable files remain generic
def test_reusable_instructions_have_no_poc_or_personal_profile_branches():
    """Keep demonstration identifiers out of shared instructions and Python."""

    prohibited = (
        "KAN-7",
        "ruhan",
        "flight-delay",
        "flight_delay",
        "qa-poc-github",
        "postgres-personal",
        "snowflake-personal",
    )
    reusable_paths = (
        REPOSITORY_ROOT / "Basic_Instructions.md",
        WORKFLOW_TEMPLATE_PATH,
        COPILOT_INSTRUCTIONS_PATH,
        *(REPOSITORY_ROOT / "modules").glob("*.py"),
    )
    for path in reusable_paths:
        content = path.read_text(encoding="utf-8").casefold()
        for value in prohibited:
            assert value.casefold() not in content, f"Found {value!r} in {path.name}"
# endregion Function: Test reusable files remain generic


# region Function: Test additive route configuration
def test_poc_configuration_parses_without_changing_routing_contract():
    """Retain routing compatibility while storing only non-secret route values."""

    config = _load_config()

    assert config["workflow_routing"] == EXPECTED_WORKFLOW_ROUTING
    routes = config["route_selected_configuration"]
    assert len(routes) == 1
    route = routes[0]
    assert route["routing"] == {
        "client_name": "ruhan",
        "project_type": "poc",
        "workflow_variant": None,
    }
    assert route["jira"]["retrieval_mode"] == "direct_issue"
    assert route["input_repository"]["credential_environment_variable"] == (
        "QA_POC_GITHUB_TOKEN"
    )
    assert route["input_repository"]["allowed_extensions"] == [".md", ".json", ".sql"]
    assert {target["db_type"] for target in route["database_targets"]} == {
        "postgresql",
        "snowflake",
    }
    assert route["required_report_dependencies"] == ["openpyxl"]
# endregion Function: Test additive route configuration


# region Function: Test protected mirror paths are route selected
def test_protected_attachment_mirrors_exist_only_in_poc_route_configuration():
    """Confine exact demonstration attachment paths to selected configuration."""

    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    route = _load_config()["route_selected_configuration"][0]
    mirrors = route["protected_attachment_mirrors"]
    mirror_root = "/".join(("qa_packages", "flight_delay_poc", "supporting_documents"))
    expected_paths = {
        f"{mirror_root}/Flight_Delay_Request_Deployment_Document.docx",
        f"{mirror_root}/Flight_Delay_Developer_Unit_Test_Results.xlsx",
    }

    assert {item["path"] for item in mirrors} == expected_paths
    for mirror_path in expected_paths:
        assert config_text.count(mirror_path) == 1
        for path in (
            REPOSITORY_ROOT / "Basic_Instructions.md",
            WORKFLOW_TEMPLATE_PATH,
            POC_WORKFLOW_PATH,
            COPILOT_INSTRUCTIONS_PATH,
            PORTABLE_BOOTSTRAP_PATH,
        ):
            assert mirror_path not in path.read_text(encoding="utf-8")
# endregion Function: Test protected mirror paths are route selected


# region Function: Test abandoned modules remain absent
def test_abandoned_hardening_modules_remain_absent():
    """Avoid introducing a second orchestration framework for minimal hardening."""

    for filename in (
        "preflight.py",
        "framework_config.py",
        "runtime_state.py",
        "approval_packets.py",
    ):
        assert not (REPOSITORY_ROOT / "modules" / filename).exists()
# endregion Function: Test abandoned modules remain absent
