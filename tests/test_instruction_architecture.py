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
EXAMPLE_CONFIG_PATH = REPOSITORY_ROOT / "ticket_run_config.example.json"
COPILOT_INSTRUCTIONS_PATH = REPOSITORY_ROOT / ".github" / "copilot-instructions.md"
POC_WORKFLOW_RELATIVE_PATH = "skills/workflows/ruhan_poc_qaworkflow.md"
POC_WORKFLOW_PATH = REPOSITORY_ROOT / POC_WORKFLOW_RELATIVE_PATH
WORKFLOW_TEMPLATE_PATH = REPOSITORY_ROOT / "skills" / "workflows" / "clientname_project_qaworkflow.md"
CONTRACT_PATHS = (
    REPOSITORY_ROOT / "Basic_Instructions.md",
    REPOSITORY_ROOT / "docs" / "prd.md",
    REPOSITORY_ROOT / "docs" / "Add_Agent_Skills.md",
    REPOSITORY_ROOT / "skills" / "workflows" / "clientname_project_qaworkflow.md",
    CONFIG_PATH,
    EXAMPLE_CONFIG_PATH,
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
    "approval_metadata_exempt_workflows": [],
    "agent_skills_root": "skills/agent_skills",
    "skill_instruction_filename": "SKILL.md",
}
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
AUDITED_TEXT_SUFFIXES = {
    ".cfg",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
AUDIT_EXCLUDED_DIRECTORIES = {
    ".agents",
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest-tmp",
    ".pytest_cache",
    ".test-runtime",
    ".venv",
    "__pycache__",
    "htmlcov",
    "logs",
    "output",
    "ticket_runs",
}
# endregion Imports and module setup


# region Function: Load ticket-run configuration
def _load_config() -> dict[str, object]:
    """Load the shared ticket-run configuration as a JSON object."""

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
# endregion Function: Load ticket-run configuration


# region Function: Load example run configuration
def _load_example_config() -> dict[str, object]:
    """Load the placeholder-only run-specific configuration example."""

    return json.loads(EXAMPLE_CONFIG_PATH.read_text(encoding="utf-8"))
# endregion Function: Load example run configuration


# region Function: Value is present
def _value_is_present(value: object) -> bool:
    """Return whether a required run-configuration value is non-empty."""

    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True
# endregion Function: Value is present


# region Function: Validate run configuration fixture
def _validate_run_configuration_fixture(run_config: dict[str, object]) -> list[str]:
    """Return full paths for values missing from a fixture under the shared schema."""

    schema = _load_config()["run_configuration_schema"]
    missing: list[str] = []

    approval = run_config.get("configuration_approval")
    approval_fields = _load_config()["run_specific_configuration"][
        "required_non_null_approval_fields"
    ]
    if not isinstance(approval, dict):
        missing.append("configuration_approval")
    else:
        for field in approval_fields:
            if not _value_is_present(approval.get(field)):
                missing.append(f"configuration_approval.{field}")

    routing = run_config.get("routing")
    if not isinstance(routing, dict):
        missing.append("routing")
    else:
        for field in schema["routing"]["required_fields"]:
            if not _value_is_present(routing.get(field)):
                missing.append(f"routing.{field}")

    jira = run_config.get("jira")
    if not isinstance(jira, dict):
        missing.append("jira")
    else:
        for field in schema["jira"]["required_fields"]:
            if not _value_is_present(jira.get(field)):
                missing.append(f"jira.{field}")
        identifier_fields = schema["jira"]["at_least_one_required_field"]
        if not any(_value_is_present(jira.get(field)) for field in identifier_fields):
            missing.append("jira.site_url_or_cloud_id")

    input_sources = run_config.get("input_sources", [])
    if not isinstance(input_sources, list):
        missing.append("input_sources")
    else:
        source_schema = schema["input_sources"]
        for index, source in enumerate(input_sources):
            if not isinstance(source, dict):
                missing.append(f"input_sources[{index}]")
                continue
            source_type = source.get("source_type")
            if source_type not in source_schema["supported_source_types"]:
                missing.append(f"input_sources[{index}].source_type")
                continue
            required_fields = source_schema[f"{source_type}_required_fields"]
            for field in required_fields:
                if not _value_is_present(source.get(field)):
                    missing.append(f"input_sources[{index}].{field}")

    database_targets = run_config.get("database_targets", [])
    if not isinstance(database_targets, list):
        missing.append("database_targets")
    else:
        required_fields = schema["database_targets"]["required_fields_when_declared"]
        for index, target in enumerate(database_targets):
            if not isinstance(target, dict):
                missing.append(f"database_targets[{index}]")
                continue
            for field in required_fields:
                if not _value_is_present(target.get(field)):
                    missing.append(f"database_targets[{index}].{field}")

    return missing
# endregion Function: Validate run configuration fixture


# region Function: Valid run configuration fixture
def _valid_run_configuration_fixture(workflow_variant: str | None = None) -> dict[str, object]:
    """Build a complete generic route fixture without a real client or environment."""

    return {
        "configuration_approval": {
            "approved_by": "authorized-reviewer",
            "approved_on": "2030-01-01",
        },
        "routing": {
            "client_name": "example-client",
            "project_type": "example-project",
            "workflow_variant": workflow_variant,
        },
        "jira": {
            "site_url": "https://jira.example.invalid",
            "cloud_id": None,
            "retrieval_mode": "direct_issue",
            "issue_key": "EXAMPLE-1",
        },
        "input_sources": [
            {
                "source_type": "github_package",
                "repository": "example-owner/example-inputs",
                "ref": "example-ref",
                "package_path": "packages/example-package",
                "authentication_profile": "example-auth-profile",
                "credential_environment_variable": "EXAMPLE_REPOSITORY_TOKEN",
                "allowed_extensions": [".sql"],
            }
        ],
        "database_targets": [
            {
                "connection_profile": "example-database-profile",
                "db_type": "example-database-type",
                "database": "example_database",
                "schema": "example_schema",
                "source_object": "example_schema.source_object",
                "target_object": "example_schema.target_object",
            }
        ],
        "workflow_approval": {"approval_metadata_exempt_workflows": []},
        "required_report_dependencies": [],
    }
# endregion Function: Valid run configuration fixture


# region Function: Test finalized workflow-routing configuration
def test_workflow_routing_uses_finalized_contract():
    """Require the exact routing object and remove its obsolete duplicate contract."""

    config = _load_config()

    assert config["workflow_routing"] == EXPECTED_WORKFLOW_ROUTING
    assert config["input_acquisition"] == EXPECTED_INPUT_ACQUISITION
    assert "agent_skill_resolution" not in config
# endregion Function: Test finalized workflow-routing configuration


# region Function: Test configured instruction paths
def test_configured_instruction_paths_exist():
    """Ensure routing roots and the non-active workflow template exist."""

    config = _load_config()
    routing = config["workflow_routing"]
    local_policy = config["run_specific_configuration"]

    assert (REPOSITORY_ROOT / routing["workflows_root"]).is_dir()
    assert (REPOSITORY_ROOT / routing["workflow_template"]).is_file()
    assert (REPOSITORY_ROOT / routing["agent_skills_root"]).is_dir()
    assert routing["skill_instruction_filename"] == "SKILL.md"
    assert REPOSITORY_ROOT / local_policy["example_path"] == EXAMPLE_CONFIG_PATH
    assert EXAMPLE_CONFIG_PATH.is_file()
# endregion Function: Test configured instruction paths


# region Function: Test approval-metadata exemptions default to none
def test_approval_metadata_exemptions_default_to_none():
    """Require local approval before null workflow-approval metadata is exempted."""

    routing = _load_config()["workflow_routing"]
    example = _load_example_config()

    assert routing["approval_metadata_exempt_workflows"] == []
    assert example["workflow_approval"]["approval_metadata_exempt_workflows"] == []
    assert example["configuration_approval"] == {
        "approved_by": None,
        "approved_on": None,
    }
    assert POC_WORKFLOW_PATH.is_file()

    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")
    frontmatter = workflow.split("---", 2)[1]
    assert 'document_type: "qa_workflow"' in frontmatter
    assert "approved_by: null" in frontmatter
    assert "approved_on: null" in frontmatter
# endregion Function: Test approval-metadata exemptions default to none


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
def test_selection_context_execution_report_and_write_approvals_remain_separate():
    """Keep input, context, execution, report, and write authorization boundaries explicit."""

    config = _load_config()
    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert [item["id"] for item in config["human_approval_checkpoints"]] == [
        "ticket_context_complete",
        "database_execution",
        "write_operation",
    ]
    assert workflow.count("**Human approval required:** `true`") == 4
    assert "Approve the proposed input selection." in workflow
    assert "Approve context." in workflow
    assert "Approve the proposed read-only execution scope. No DDL or DML." in workflow
    assert "Approve the proposed report export." in workflow
    assert "failures are blockers rather than approval checkpoints" in workflow
# endregion Function: Test genuine approval checkpoints


# region Function: Test report-export approval scope
def test_report_export_requires_separate_explicit_approval():
    """Require a recorded report proposal and decision before final export."""

    workflow = POC_WORKFLOW_PATH.read_text(encoding="utf-8")
    approval = workflow.index("Approve the proposed report export.")
    generation = workflow.index("Generate the approved HTML, Excel, or other final report")

    for required_detail in (
        "proposed report format",
        "destination path",
        "evidence or data to include",
        "whether sensitive information is present",
        "required redactions",
    ):
        assert required_detail in workflow
    for prior_decision in (
        "context approval",
        "input-selection approval",
        "SQL execution approval",
        "database write approval",
        "profile-switch approval",
    ):
        assert prior_decision in workflow
    assert "Silence is not approval" in workflow
    assert "Rejection prevents report creation" in workflow
    assert approval < generation
# endregion Function: Test report-export approval scope


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
        "workflow-specific input state",
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
        CONFIG_PATH,
        EXAMPLE_CONFIG_PATH,
        WORKFLOW_TEMPLATE_PATH,
        COPILOT_INSTRUCTIONS_PATH,
        *(REPOSITORY_ROOT / "modules").glob("*.py"),
    )
    for path in reusable_paths:
        content = path.read_text(encoding="utf-8").casefold()
        for value in prohibited:
            assert value.casefold() not in content, f"Found {value!r} in {path.name}"
# endregion Function: Test reusable files remain generic


# region Function: Test shared configuration is parameterized
def test_shared_configuration_contains_no_selected_route_or_demo_values():
    """Keep real client, ticket, repository, Jira, and database values out of shared config."""

    config = _load_config()
    shared_text = CONFIG_PATH.read_text(encoding="utf-8").casefold()
    example_text = EXAMPLE_CONFIG_PATH.read_text(encoding="utf-8").casefold()
    prohibited_values = (
        "route_selected_configuration",
        "kan-7",
        "ruhan",
        "flight_delay",
        "qa-poc-github",
        "qa_poc_github_token",
        "atlassian.net",
        "qa_automation_poc_inputs",
        "raw.flights",
        "analytics.flight_performance",
    )

    assert config["workflow_routing"] == EXPECTED_WORKFLOW_ROUTING
    for value in prohibited_values:
        assert value not in shared_text
        assert value not in example_text
# endregion Function: Test shared configuration is parameterized


# region Function: Test selected route values remain out of reusable repository files
def test_selected_route_values_remain_out_of_reusable_repository_files():
    """Confine known POC route values to explicit tests or the named client workflow."""

    test_relative_path = "tests/test_instruction_architecture.py"
    manual_workflow_test_path = "tests/test_manual_input_workflow.py"
    allowed_paths_by_value = {
        "ruhan": {
            POC_WORKFLOW_RELATIVE_PATH,
            test_relative_path,
            manual_workflow_test_path,
        },
        "kan-7": {test_relative_path},
        "ruhannaik444.atlassian.net": {test_relative_path},
        "51cd9d76-2810-472a-8b50-b2412c213a7f": {test_relative_path},
        "rnnaik1102-droid/qa_automation_poc_inputs": {test_relative_path},
        "qa_packages/flight_delay_poc": {test_relative_path},
        "qa-poc-github": {test_relative_path},
        "qa_poc_github_token": {test_relative_path},
        "raw.flights": {test_relative_path},
        "analytics.flight_performance": {test_relative_path},
        "flight_delay_request_deployment_document.docx": {test_relative_path},
        "flight_delay_developer_unit_test_results.xlsx": {test_relative_path},
    }

    for path in REPOSITORY_ROOT.rglob("*"):
        relative_path = path.relative_to(REPOSITORY_ROOT).as_posix()
        if not path.is_file() or any(part in AUDIT_EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        if path.name == ".env" or (
            path.name != ".gitignore" and path.suffix.casefold() not in AUDITED_TEXT_SUFFIXES
        ):
            continue

        content = path.read_text(encoding="utf-8", errors="ignore").casefold()
        for value, allowed_paths in allowed_paths_by_value.items():
            if value in content:
                assert relative_path in allowed_paths, (
                    f"Selected route value {value!r} must not appear in {relative_path}."
                )
# endregion Function: Test selected route values remain out of reusable repository files


# region Function: Test explicit run configuration satisfies schema
def test_explicit_run_configuration_supplies_required_values_and_optional_variant():
    """Accept complete generic run values with or without a workflow variant."""

    assert _validate_run_configuration_fixture(_valid_run_configuration_fixture()) == []
    variant_config = _valid_run_configuration_fixture("regional")
    assert _validate_run_configuration_fixture(variant_config) == []
    assert variant_config["routing"]["workflow_variant"] == "regional"
# endregion Function: Test explicit run configuration satisfies schema


# region Function: Test missing run values are named clearly
def test_missing_required_run_values_return_full_field_paths():
    """Name missing core values without treating unused optional arrays as errors."""

    missing = _validate_run_configuration_fixture(_load_example_config())

    assert "configuration_approval.approved_by" in missing
    assert "configuration_approval.approved_on" in missing
    assert "routing.client_name" in missing
    assert "routing.project_type" in missing
    assert "jira.issue_key" in missing
    assert "jira.site_url_or_cloud_id" in missing
    assert "input_sources[0].repository" not in missing
    assert "database_targets[0].database" not in missing
# endregion Function: Test missing run values are named clearly


# region Function: Test runtime resolution precedence
def test_runtime_resolution_precedence_is_explicit_and_never_guesses():
    """Keep authoritative Jira first and make unresolved conflicts blocking."""

    config = _load_config()
    resolution = config["runtime_resolution"]
    instructions = (REPOSITORY_ROOT / "Basic_Instructions.md").read_text(encoding="utf-8")

    assert resolution["precedence"] == [
        "authoritative_jira_ticket_context",
        "selected_approved_workflow",
        "explicit_run_specific_configuration",
        "authorized_user_clarification",
        "never_guess",
    ]
    assert resolution["lower_precedence_values_may_only_fill_missing_fields"] is True
    assert resolution["missing_required_behavior"] == "block_before_workspace_initialization"
    assert "Report every missing field by its full path" in instructions
# endregion Function: Test runtime resolution precedence


# region Function: Test local configuration remains secret-free and relative
def test_local_configuration_is_gitignored_secret_free_and_repository_relative():
    """Keep the optional local route file portable and outside version control."""

    config = _load_config()
    local_policy = config["run_specific_configuration"]
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    example = _load_example_config()
    prohibited_secret_keys = {
        "token",
        "password",
        "cookie",
        "private_key",
        "connection_string",
        "credential_value",
        "secret",
    }

    # region Function: Inspect example values
    def inspect(value: object) -> None:
        """Reject raw-secret field names anywhere in the committed example."""

        if isinstance(value, dict):
            for key, child in value.items():
                assert key.casefold() not in prohibited_secret_keys
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
    # endregion Function: Inspect example values

    inspect(example)
    assert local_policy["secrets_allowed"] is False
    assert local_policy["local_override_path"] in gitignore.splitlines()
    assert example["input_sources"] == []
    assert example["database_targets"] == []
    for configured_path in (
        config["ticket_runs_root"],
        config["logs_root"],
        config["output_root"],
        local_policy["example_path"],
        local_policy["local_override_path"],
        config["workflow_routing"]["workflows_root"],
        config["workflow_routing"]["workflow_template"],
        config["workflow_routing"]["agent_skills_root"],
    ):
        assert not Path(configured_path).is_absolute()
        assert ".." not in Path(configured_path).parts
        assert "\\" not in configured_path
# endregion Function: Test local configuration remains secret-free and relative


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
