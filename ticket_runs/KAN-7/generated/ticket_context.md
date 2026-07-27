# Ticket Context: KAN-7

## Workflow Selection

- Selected workflow: `skills/workflows/ruhan_poc_qaworkflow.md`
- Selection basis: direct Jira retrieval of `KAN-7` confirmed `client_name: ruhan`, `project_type: poc`, and `workflow_variant: null`.
- Administrative approval metadata: workflow path is listed in `ticket_run_config.json` under `workflow_routing.approval_metadata_exempt_workflows`.
- Workflow status reached: consolidated context prepared; context approval is pending.

## Jira Business Request

Source role: Jira business request

- Jira key: `KAN-7`
- Jira URL: `https://ruhannaik444.atlassian.net/browse/KAN-7`
- Summary: Validate 2015 Flight Delay Analytics Transformation Across PostgreSQL and Snowflake
- Issue type: Task
- Status at retrieval: To Do
- Priority: Medium
- Reporter: Ruhan Naik
- Created: 2026-07-26T10:05:12.711+0530
- Updated: 2026-07-26T11:57:23.059+0530

Business request:

Validate the flight-delay analytics implementation across PostgreSQL and Snowflake before downstream reporting and analysis approval. The implementation uses the 2015 Flight Delays and Cancellations dataset and should produce an analytics-ready flight-performance output with consistent results across both database platforms.

Acceptance criteria from Jira:

1. The complete source flight population is represented in the analytics output.
2. PostgreSQL and Snowflake produce consistent business-level results.
3. Cancelled, diverted, on-time, and delayed flights are classified correctly.
4. Airline and airport information is represented correctly.
5. Data-quality issues are identified consistently.
6. Any unexplained differences between PostgreSQL and Snowflake are documented.
7. QA evidence and final validation results are provided for review.

## Declared Supporting Sources

Source role: technical implementation specification

- Jira attachment: `Flight_Delay_Request_Deployment_Document.docx`
- Attachment id: `10001`
- Jira-reported size: 39970 bytes
- Availability in this run: unresolved. The repository has no configured non-secret direct-file downloader authentication profile for Atlassian attachment bytes, and no Atlassian binary attachment download tool is exposed in the current toolset.
- Configured protected mirror: `qa_packages/flight_delay_poc/supporting_documents/Flight_Delay_Request_Deployment_Document.docx`
- Mirror status: bootstrap reference only; not reviewed content because actual DOCX bytes were not acquired and validated under `downloads/`.

Source role: developer unit-test evidence

- Jira attachment: `Flight_Delay_Developer_Unit_Test_Results.xlsx`
- Attachment id: `10000`
- Jira-reported size: 7094 bytes
- Availability in this run: unresolved. The repository has no configured non-secret direct-file downloader authentication profile for Atlassian attachment bytes, and no Atlassian binary attachment download tool is exposed in the current toolset.
- Configured protected mirror: `qa_packages/flight_delay_poc/supporting_documents/Flight_Delay_Developer_Unit_Test_Results.xlsx`
- Mirror status: bootstrap reference only; not reviewed content because actual XLSX bytes were not acquired and validated under `downloads/`.

Source role: QA package

- Repository: `rnnaik1102-droid/QA_Automation_POC_Inputs`
- Ref: `main`
- Package path: `qa_packages/flight_delay_poc`
- Authentication profile: `qa-poc-github`
- Credential environment variable reference: `QA_POC_GITHUB_TOKEN`
- Allowed acquired extensions: `.md`, `.json`, `.sql`
- Acquisition status: completed through `modules.download_ticket_inputs github-package`.
- Archive path: `ticket_runs/KAN-7/downloads/source_archives/rnnaik1102-droid-QA_Automation_POC_Inputs-main-0d6e4079e3.zip`
- Archive size: 10296 bytes
- Archive SHA-256: `4d31c82ed34630754c9389d7466a3ffd36d5ce02634d1ee15eacaa39ced27f6d`
- Manifest path: `ticket_runs/KAN-7/generated/download_manifest.json`

## QA Package Inventory

Source artifact: `ticket_runs/KAN-7/downloads/qa_scripts/package_manifest.json`

- Package name: `flight_delay_poc`
- Package version: `1.0`
- Automatic execution: `false`
- Extracted files: 15

Extracted files:

- `README.md`
- `package_manifest.json`
- `parameters.example.json`
- `postgresql/01_setup_validation.sql`
- `postgresql/02_pre_qa_checks.sql`
- `postgresql/03_post_qa_checks.sql`
- `postgresql/04_reconciliation.sql`
- `postgresql/05_duplicate_and_rule_checks.sql`
- `postgresql/06_scratch_write_test.sql`
- `snowflake/01_setup_validation.sql`
- `snowflake/02_pre_qa_checks.sql`
- `snowflake/03_post_qa_checks.sql`
- `snowflake/04_reconciliation.sql`
- `snowflake/05_duplicate_and_rule_checks.sql`
- `snowflake/06_scratch_write_test.sql`

Package rules from `README.md`:

- Preserve original downloaded files under `ticket_runs/<ticket-id>/downloads/`.
- Do not execute downloaded SQL automatically.
- Resolve tokens only from approved ticket context.
- Prepare controlled SQL under `generated/`.
- Obtain separate execution approval.
- Execute one statement per MCP call.

## Candidate Database Targets From Routing

Source artifact: `ticket_run_config.json`

PostgreSQL target:

- Database type: `postgresql`
- Database: `flight_delay_poc`
- Source object: `raw.flights`
- Target object: `analytics.flight_performance`
- QA schema: `qa`

Snowflake target:

- Database type: `snowflake`
- Database: `FLIGHT_DELAY_POC`
- Source object: `RAW.FLIGHTS`
- Target object: `ANALYTICS.FLIGHT_PERFORMANCE`
- QA schema: `QA`

Source artifact: `parameters.example.json`

- Raw schema: `raw`
- Analytics schema: `analytics`
- QA schema: `qa`
- Source airline table: `airlines`
- Source airport table: `airports`
- Source flights table: `flights`
- Target table: `flight_performance`
- Expected flight rows: `5819079`

## QA-Relevant SQL Source Review

Source artifacts: SQL files under `ticket_runs/KAN-7/downloads/qa_scripts/`

Read-only source material identified:

- PostgreSQL and Snowflake setup validation queries check current database context and existence of source and target objects.
- PostgreSQL and Snowflake pre-QA checks count raw source rows and source flight states.
- PostgreSQL and Snowflake post-QA checks count analytics rows and flight classification outputs.
- PostgreSQL and Snowflake reconciliation queries compare raw and analytics row counts.
- PostgreSQL and Snowflake duplicate/rule checks inspect duplicate flight identifiers and classification/data-quality rule indicators.

Write-classified source material identified:

- `postgresql/06_scratch_write_test.sql` contains `CREATE TABLE`, `INSERT`, `UPDATE`, `DELETE`, and `DROP TABLE`.
- `snowflake/06_scratch_write_test.sql` contains `CREATE TABLE`, `INSERT`, `UPDATE`, `DELETE`, and `DROP TABLE`.
- These scratch write tests are excluded from any read-only execution scope unless separately and explicitly authorized as write/DDL/DML operations.

Unresolved tokens observed:

- `{{SCRATCH_TABLE}}` appears in scratch write-test SQL and has no approved value in the current context.
- Other package tokens map to route configuration and `parameters.example.json`, but they still require context approval before controlled SQL is generated.

## Proposed QA Scope For Approval

Approve as in scope:

- Prepare a QA plan for validating source population completeness, target row counts, classification outputs, duplicate/rule checks, source-to-target reconciliation, and cross-platform PostgreSQL/Snowflake comparison.
- Use Jira as the business request and the downloaded QA package as inert source material.
- Use route-configured database targets and package parameter examples as candidate context for planning.
- After context approval, resolve the required `qa-test-planner` Agent Skill for QA planning.
- Keep all SQL preparation under `ticket_runs/KAN-7/generated/generated_sql/`.
- Require a separate database profile discovery and execution approval checkpoint before any database MCP execution.

Exclude or block from current scope:

- Do not execute any SQL from `downloads/` directly.
- Do not execute any DDL, DML, scratch table, or environment-changing statement under read-only approval.
- Do not claim review of the DOCX technical implementation specification or XLSX developer unit-test evidence until actual bytes are supplied and validated under `downloads/`.
- Do not proceed to QA planning if the missing attachment review is considered action-critical by the approver.

## Contradictions

- No contradictory action-critical values were found between Jira, route configuration, and the downloaded QA package.
- The configured protected attachment mirrors are not treated as evidence because actual DOCX/XLSX bytes were not acquired and validated.

## Unresolved Questions

1. Are the missing Jira attachment bytes action-critical for QA planning, or may planning proceed using Jira plus the downloaded QA package only?
2. If attachment review is required, an authorized user must place `Flight_Delay_Request_Deployment_Document.docx` and `Flight_Delay_Developer_Unit_Test_Results.xlsx` under `ticket_runs/KAN-7/downloads/` so their type, size, and SHA-256 can be validated before review.
3. Database MCP profile mappings for PostgreSQL and Snowflake have not been discovered yet; the selected workflow performs that only at the execution-approval checkpoint after QA planning and SQL preparation.
4. Scratch write-test execution is not approved and lacks an approved `SCRATCH_TABLE` value.

## Downloaded Source Files Reviewed

- Reviewed as text only: `README.md`, `package_manifest.json`, `parameters.example.json`, and SQL files under `ticket_runs/KAN-7/downloads/qa_scripts/`.
- Not executed: all downloaded SQL files.
- Not reviewed: Jira DOCX and XLSX attachment bytes, because they are not present under `downloads/`.

## User Review

Approval status: Approved at 2026-07-26T16:55:00.0398021Z.

Approved scope note: context is approved using Jira and the validated QA package only. The unresolved DOCX and XLSX attachments are not action-critical for this read-only planning and validation run and must not be claimed as reviewed.
