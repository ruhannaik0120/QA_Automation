# QA Plan: KAN-7

## Planning Basis

- Workflow: `skills/workflows/ruhan_poc_qaworkflow.md`
- Required Agent Skill used: `qa-test-planner`
- Approved context checkpoint: `ticket_context_complete`, approved at `2026-07-26T16:55:00.0398021Z`
- Approved sources: Jira business request and validated GitHub QA package only
- Not reviewed: `Flight_Delay_Request_Deployment_Document.docx` and `Flight_Delay_Developer_Unit_Test_Results.xlsx`
- Execution posture: read-only validation planning. No database execution is approved by this plan.

## Objectives

1. Verify the complete 2015 source flight population is represented in the analytics target.
2. Validate PostgreSQL and Snowflake produce consistent business-level results.
3. Confirm cancelled, diverted, on-time, delayed, and data-quality classifications are measurable and comparable.
4. Identify missing airline and airport lookup results in the analytics output.
5. Record any unexplained PostgreSQL/Snowflake differences as evidence for review.

## In Scope

- PostgreSQL target from routing: `flight_delay_poc`, source `raw.flights`, target `analytics.flight_performance`, QA schema `qa`.
- Snowflake target from routing: `FLIGHT_DELAY_POC`, source `RAW.FLIGHTS`, target `ANALYTICS.FLIGHT_PERFORMANCE`, QA schema `QA`.
- Read-only setup validation, source row checks, target row/classification checks, reconciliation checks, duplicate/rule checks, and cross-platform comparison.
- Controlled SQL generation from approved context and inert QA package source material.

## Out Of Scope

- Review claims for DOCX/XLSX attachments that were not acquired as bytes.
- Execution of any SQL from `ticket_runs/KAN-7/downloads/`.
- Scratch write tests, DDL, DML, or environment-changing commands under read-only approval.
- Database execution before separate profile discovery and explicit execution approval.

## Entry Criteria

- Ticket workspace initialized.
- Jira business request retrieved directly.
- QA package downloaded through `modules.download_ticket_inputs` and represented in `download_manifest.json`.
- Context approval recorded in `approval_log.md`.
- Database profile discovery remains pending and is required before execution approval.

## Exit Criteria For This Read-Only Validation Run

- Every proposed executable statement is token-resolved, singular, read-only, and traceable to this plan.
- Execution scope is separately approved before any MCP database execution.
- Results, skipped checks, blocked checks, and unresolved facts are reported honestly.
- Cross-platform result differences are documented with check IDs and safe evidence.

## Stop Conditions

- Missing, zero, or multiple database profile matches for a configured target.
- Connection metadata does not match the approved target.
- SQL guard rejects a statement.
- A generated statement hash changes after execution approval.
- Any statement contains unresolved tokens.
- Any statement attempts DDL, DML, scratch-table setup, or environment-changing behavior without separate write authorization.
- PostgreSQL and Snowflake results cannot be compared due to missing evidence.

## Planned Checks

| Check ID | Platform | Source package file | Permission | Objective | Expected outcome | Evidence |
|---|---|---|---|---|---|---|
| PG-RO-001 | PostgreSQL | `postgresql/01_setup_validation.sql` | read-only | Confirm connected database and required source/target objects exist. | Database is `flight_delay_poc`; `raw.flights` exists; `analytics.flight_performance` exists. | One result row with object-existence booleans. |
| PG-RO-002 | PostgreSQL | `postgresql/02_pre_qa_checks.sql` | read-only | Count raw source rows and blank key input fields. | `raw_flight_rows = 5819079`; blank-field counts captured for data-quality evidence. | One result row with source counts. |
| PG-RO-003 | PostgreSQL | `postgresql/03_post_qa_checks.sql` | read-only | Count analytics rows, classifications, lookup misses, and data-quality flags. | Analytics rows are present and classification/lookup metrics are captured. | One result row with target metrics. |
| PG-RO-004 | PostgreSQL | `postgresql/04_reconciliation.sql` | read-only | Compare raw and analytics row counts. | `row_difference = 0`. | One result row with raw rows, analytics rows, and row difference. |
| PG-RO-005 | PostgreSQL | `postgresql/05_duplicate_and_rule_checks.sql` | read-only | Check null/duplicate flight keys and core rule indicators. | `null_flight_keys = 0`; duplicate and business-rule exception counts captured for review. | One result row with rule-check counts. |
| SF-RO-001 | Snowflake | `snowflake/01_setup_validation.sql` | read-only | Confirm connected database and required source/target objects exist. | Database is `FLIGHT_DELAY_POC`; `RAW.FLIGHTS` exists; `ANALYTICS.FLIGHT_PERFORMANCE` exists. | One result row with object-existence counts. |
| SF-RO-002 | Snowflake | `snowflake/02_pre_qa_checks.sql` | read-only | Count raw source rows and blank key input fields. | `RAW_FLIGHT_ROWS = 5819079`; blank-field counts captured for data-quality evidence. | One result row with source counts. |
| SF-RO-003 | Snowflake | `snowflake/03_post_qa_checks.sql` | read-only | Count analytics rows, classifications, lookup misses, and data-quality flags. | Analytics rows are present and classification/lookup metrics are captured. | One result row with target metrics. |
| SF-RO-004 | Snowflake | `snowflake/04_reconciliation.sql` | read-only | Compare raw and analytics row counts. | `ROW_DIFFERENCE = 0`. | One result row with raw rows, analytics rows, and row difference. |
| SF-RO-005 | Snowflake | `snowflake/05_duplicate_and_rule_checks.sql` | read-only | Check null/duplicate flight keys and core rule indicators. | `NULL_FLIGHT_KEYS = 0`; duplicate and business-rule exception counts captured for review. | One result row with rule-check counts. |
| XP-RO-001 | Cross-platform | Derived from PG/SF results | read-only comparison only | Compare PostgreSQL and Snowflake business-level outputs. | Comparable metrics match or differences are explained. | Comparison table derived from normalized execution results. |
| BLOCK-WRITE-001 | PostgreSQL/Snowflake | `*/06_scratch_write_test.sql` | DDL/DML/write | Scratch write behavior. | Blocked for this read-only run. | Approval log records exclusion; no write execution. |

## Minimum QA Coverage Matrix

| Category | Status | Planned coverage or reason |
|---|---|---|
| Database, schema, and object existence | applicable | PG-RO-001 and SF-RO-001 validate database context and source/target object existence. |
| Column names, data types, lengths, precision, scale, and nullability | blocked | The approved sources do not provide column metadata statements or attachment details; database metadata inspection can be added only after profile discovery and approval. |
| Source and target row counts | applicable | PG-RO-002, PG-RO-003, PG-RO-004, SF-RO-002, SF-RO-003, and SF-RO-004. |
| Null checks | applicable | Blank source fields, missing lookup names, null flight keys, and cancellation-reason checks are included. |
| Duplicate and uniqueness checks | applicable | PG-RO-005 and SF-RO-005 count duplicate `flight_key` values. |
| Primary-key and referential-integrity checks | blocked | No approved PK/FK metadata or relationship specification is available; lookup-miss counts provide partial business evidence only. |
| Source-to-target mappings | applicable | Reconciliation checks and classification/count checks validate mapped business outputs at aggregate level. |
| Transformations and business rules | applicable | Cancellation, diversion, on-time, data-quality, cancellation-reason, and same-origin/destination checks are included. |
| Aggregate and reconciliation checks | applicable | Row-count reconciliation and cross-platform aggregate comparison are included. |
| Incremental-load behaviour | not_applicable | Jira/package context identifies a 2015 dataset validation, not incremental load behavior. |
| Idempotency and safe rerun behaviour | blocked | Scratch write tests are excluded; no approved idempotency evidence or rerun specification is available for read-only validation. |
| Audit columns, timestamps, and load identifiers | blocked | No approved audit-column names or expected values are available from Jira/package context. |
| Boundary and negative cases | applicable | Blank source field counts, missing lookups, null keys, duplicate keys, cancelled-without-reason, and same-origin/destination checks provide negative/data-quality coverage. |
| Performance checks only when required by authoritative context | not_applicable | No authoritative performance requirement is included in Jira or the validated QA package. |
| Rollback and recovery behaviour | not_applicable | No write, deployment, rollback, or recovery operation is approved for this read-only run. |

## Evidence Capture Requirements

- For each executed check, capture check ID, platform, approved profile, normalized SQL, statement hash, row count, result payload, duration, validation status, and any secret-safe error.
- Store normalized execution evidence in `ticket_runs/KAN-7/generated/execution_results/execution_result.json`.
- Store final reports only under `output/KAN-7/` if reporting is reached after execution is approved, completed, skipped, rejected, or blocked.

## Approval Boundaries

- This QA plan does not approve database execution.
- The next workflow step may prepare controlled, read-only SQL statements.
- Execution requires database profile discovery and the exact prompt: `Approve the proposed read-only execution scope. No DDL or DML.`
- Any DDL, DML, scratch table, or environment-changing operation requires separate explicit write authorization and is not proposed for this run.
