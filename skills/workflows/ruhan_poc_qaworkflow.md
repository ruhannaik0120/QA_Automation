---
document_type: "qa_workflow"
client_name: "ruhan"
project_type: "poc"
workflow_variant: null
created_by: "ruhannaik0120"
created_on: "2026-07-25"
last_edited_by: "ruhannaik0120"
last_edited_on: "2026-07-27"
version: "1.2"
workflow_owner: "ruhannaik0120"
approved_by: null
approved_on: null
---

# Jira-Driven QA Automation POC Workflow

## Purpose

This workflow coordinates QA preparation, controlled database validation, and evidence generation for an authorized Jira ticket routed to the `ruhan` demonstration client and `poc` project type. It starts when the user supplies a Jira ticket key and remains valid across tickets whose document names, formats, environments, and validation details differ.

The workflow treats Jira as the high-level business request and uses supporting material to establish the technical details needed for QA. It does not assume that Jira contains server names, schemas, tables, package paths, execution order, or other implementation details. Those values must come from authorized sources and must be approved before use.

The procedure is client-agnostic in how it classifies inputs. It uses the permanent source roles defined below instead of relying on one client's filename:

- **Jira business request:** the high-level issue, product change, or requested work, usually created by a product owner.
- **Technical implementation specification:** the granular implementation and QA instructions completed by the developer after requirement gathering. Its client-specific name is configurable. "Request/Deployment Document" is an NCLH EDM example only; other clients may use Technical Design Document, Deployment Specification, Implementation Document, Change Specification, or another approved name.
- **Developer unit-test evidence:** developer-produced test results or evidence in an approved format such as DOCX, XLSX, PDF, CSV, screenshots, or another declared format.
- **QA package:** QA-specific tokenized or parameterized assets. It may contain SQL validation scripts, DDL, DML, setup queries, pre-QA queries, post-QA checks, reconciliation queries, data-validation queries, or ETL/data-pipeline SQL assets. A locally supplied package is untrusted source material and is never executed automatically.

## Scope

For this POC workflow only, input acquisition is declared as:

```yaml
input_acquisition:
  mode: manual
```

This declaration does not disable automatic acquisition for another workflow that explicitly selects `automatic` and satisfies its approval, authentication, and downloader-safety requirements.

This workflow applies only when authoritative context establishes:

- `client_name` as `ruhan`;
- `project_type` as `poc`, normally from the Jira title or other authoritative ticket metadata;
- no additional `workflow_variant`; and
- the supplied Jira ticket key as the ticket-run identifier.

The workflow covers:

- automatic ticket-workspace initialization;
- authorized Jira retrieval;
- discovery, role classification, explicit selection, manual placement, and local verification of supporting inputs;
- a separate input-selection approval checkpoint;
- consolidated context synthesis and conflict handling;
- a separate context-approval checkpoint;
- QA planning and conditional SQL preparation;
- a separate execution-approval checkpoint;
- controlled one-statement-at-a-time database MCP execution when applicable and approved; and
- final evidence and report preparation using existing supported project capabilities.

This workflow does not assume that every ticket includes external documents, a GitHub package, SQL, database validation, DDL, DML, HTML reports, or Excel reports. Conditional checklist items must be skipped with a recorded reason when authoritative context proves they do not apply.

This workflow is not applicable when the client, project type, or workflow variant does not match its metadata exactly. It is also not applicable to unsupported ticket categories, requests lacking an authoritative Jira key, or work that requires a different approved workflow. In those cases, the agent must stop and request clarification from the workflow owner or an authorized user.

## Prerequisites

- The global AI-orchestrated preflight in `Basic_Instructions.md` must finish successfully before this workflow starts. Authentication, configuration, connector, dependency, routing, and profile-ambiguity failures are blockers rather than approval checkpoints and must create no ticket runtime artifacts.
- The user must provide a Jira ticket key. The agent must not infer or reuse a ticket key from an unrelated run.
- The agent must have access to the repository and its existing Python environment so it can run the ticket initializer.
- Jira retrieval must use an authorized Atlassian integration. Missing authorization is blocking and must not be bypassed with guessed or cached ticket content.
- The authoritative client identity and Jira project type must exactly match this workflow's routing metadata.
- Supporting inputs must be declared by Jira, an authorized user, or another approved source. The agent must classify them by role rather than by filename alone.
- Every included remote document or package must be downloaded by an authorized user and placed under `ticket_runs/<ticket-id>/downloads/`; automatic acquisition is disabled for this workflow.
- Authentication profiles, allowed hosts, repository names, repository refs, package paths, environments, server names, database names, schemas, tables, and execution targets must come from authorized sources. Missing values are blocking.
- Database execution requires a configured database MCP profile, successful connection validation, applicable SQL-guard acceptance, and explicit execution approval.
- Write operations, DDL, DML, and environment-changing setup require their own explicit authorization. Read-only approval never implies write approval.
- The `qa-test-planner` Agent Skill is mandatory only for checklist item 7, `prepare-qa-plan`; no other checklist item requires an Agent Skill.

## Steps

The checklist below is the ticket-independent control path for this client and
project type. It initializes a resumable workspace, classifies authoritative
input references by role, records explicit input-selection approval, pauses for
manual placement, verifies local files, and synthesizes context before the
separate context-approval gate. Planning and any applicable SQL preparation occur
only after that context is approved; a later approval gate controls database
execution, and evidence and reports are produced from recorded results rather
than assumed outcomes. Each ticket records its own status and artifacts under
the paths named by the applicable checklist item.

1. **Checklist item:** Initialize the ticket workspace
   - **Checklist item ID:** `initialize-ticket-workspace`
   - **Objective:** Create the stable ticket-scoped input and generated-artifact structure before retrieving or producing ticket content.
   - **Applicability:** `required`
   - **Applicability rule:** Run once at the beginning of every ticket run and safely repeat when resuming.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[user_supplied_jira_ticket_key, global_preflight_succeeded, exact_workflow_selected]`
   - **Required inputs:** `[jira_ticket_key]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[local_python, modules.init_ticket_run, repository_filesystem]`
   - **Ordered agent actions:**
     1. Confirm that preflight validated the user-supplied Jira ticket key and selected this exact workflow.
     2. Run the existing initializer behavior equivalent to `python -m modules.init_ticket_run <ticket-key>`.
     3. Confirm that `ticket_runs/<ticket-id>/downloads/` and `ticket_runs/<ticket-id>/generated/` exist.
     4. Confirm that stable generated starter artifacts exist without replacing any pre-existing ticket artifact.
     5. Use `logs/<ticket-id>.log` as the only workflow log location.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Ticket workspace exists and existing artifacts remain unchanged.
   - **Completion evidence:** `[initializer_success, downloads_directory_present, generated_directory_present]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_report_workspace_initialization_failure`

2. **Checklist item:** Retrieve the authoritative Jira business request
   - **Checklist item ID:** `retrieve-jira-business-request`
   - **Objective:** Obtain the ticket's high-level business requirement and declared source references from Jira.
   - **Applicability:** `required`
   - **Applicability rule:** Run after workspace initialization for every supported ticket.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[initialize-ticket-workspace_completed, authorized_atlassian_access_available]`
   - **Required inputs:** `[jira_ticket_key, authorized_client_identity]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[authorized_atlassian_integration, jira]`
   - **Ordered agent actions:**
     1. Reuse the exact Jira issue payload and authorized site URL or cloud ID established by preflight; perform any freshness check through direct issue retrieval with that same identifier.
     2. Do not replace direct issue retrieval with broad Atlassian search or ask the user to repeat the configured Jira identifier.
     3. Confirm that the ticket metadata routes exactly to `client_name: ruhan`, `project_type: poc`, and no workflow variant.
     4. Record Jira as the high-level business request, not as proof of missing technical details.
     5. Retain the ticket's attachment list, description, and comments when comments are part of the authoritative retrieval so the next item can discover references without following them.
     6. Do not open attachment content, follow hyperlinks, fetch repositories, or treat any reference as inspected content during Jira retrieval.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Authoritative Jira content and its declared source inventory are available for classification.
   - **Completion evidence:** `[jira_ticket_retrieved, routing_metadata_confirmed, declared_sources_inventoried]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/ticket_context.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_authorized_jira_access_or_routing_clarification`

3. **Checklist item:** Discover, classify, and approve supporting input references
   - **Checklist item ID:** `classify-supporting-inputs`
   - **Objective:** Discover potentially relevant references, classify them, and record an explicit per-item user selection before any referenced file is read or acquired.
   - **Applicability:** `required`
   - **Applicability rule:** Run for every ticket, including tickets that declare no supporting inputs.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[retrieve-jira-business-request_completed]`
   - **Required inputs:** `[jira_business_request, jira_attachments, jira_description, retrieved_comments_when_available, approved_workflow_metadata, approved_local_configuration_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[authorized_atlassian_integration, repository_filesystem, user_conversation]`
   - **Ordered agent actions:**
     1. Discover Jira attachments; hyperlinks in the description; hyperlinks in comments when those comments were retrieved authoritatively; repository, document, spreadsheet, archive, and package links; and explicit source references in this workflow or approved local configuration.
     2. Do not follow a hyperlink, fetch a repository, download an attachment, inspect remote Word or Excel content, or assume that every Jira link is relevant.
     3. Classify each reference as a technical implementation specification, developer unit-test evidence, QA package, or another explicitly approved role.
     4. Resolve non-secret reference metadata using the precedence in `ticket_run_config.json`, treating conflicts and missing action-critical values as blocking instead of guessing.
     5. Create or resume `ticket_runs/<ticket-id>/generated/input_selection.json` as this POC workflow's durable manual-acquisition state, then write each proposed item with an item number, display name, source type, sanitized URL or Jira attachment reference, expected extension or content type, source location, relevance reason, possible authentication requirement, manual-download requirement, and required or optional status when known. Never persist tokens, signed URLs, cookies, or credentials.
     6. Present the complete proposed-input list and require the user to mark every item `include`, `exclude`, `defer`, or `unclear / needs clarification`.
     7. Ask exactly `Approve the proposed input selection.` Approval is not implied; `continue` counts only when this complete selection was already shown clearly.
     8. Record each decision, unresolved and excluded references, overall approval status, timestamp, and user-supplied approver identity without overwriting an existing approval.
     9. Do not read, acquire, or inspect excluded, deferred, unclear, or unapproved references.
     10. Record an empty approved selection when authoritative context and the user confirm that no external inputs apply.
   - **Human approval required:** `true`
   - **Human approver role:** `authorized_qa_or_project_representative`
   - **Expected checkpoint:** Every discovered reference has a recorded decision and the complete input selection is explicitly approved.
   - **Completion evidence:** `[proposed_input_list, per_item_decisions, explicit_input_selection_approval, unresolved_references_recorded, excluded_references_recorded]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/input_selection.json`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_missing_source_details`

4. **Checklist item:** Manually place and verify approved local inputs
   - **Checklist item ID:** `securely-acquire-ticket-inputs`
   - **Objective:** Pause for authorized manual placement and verify local filenames and safe metadata against the approved input selection before content inspection.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply when the approved selection contains an included input or when any unexpected file already exists under `downloads/`.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[classify-supporting-inputs_completed, explicit_input_selection_approval_recorded]`
   - **Required inputs:** `[ticket_id, approved_input_selection, ticket_downloads_directory]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[user_conversation, repository_filesystem, safe_local_file_metadata]`
   - **Ordered agent actions:**
     1. For each included item not already local, tell the user to download only the approved item, preserve its original filename and extension, place it directly in `ticket_runs/<ticket-id>/downloads/`, store no secret there, and return to confirm when all approved files are present.
     2. Pause. Do not continue merely because links were discovered or input selection was approved.
     3. After the user confirms placement, verify that the ticket `downloads/` directory exists and list every local file without opening file content or macros.
     4. Compare local files with the approved selection without assuming that a similar filename proves remote identity.
     5. Record safe local metadata including filename, extension, and size; identify exact missing items, unexpected files, duplicate names, and unsupported extensions.
     6. Stop and report each missing approved item. Do not mark it verified merely because `input_selection.json` exists.
     7. For every unexpected file, ask whether it should be included before reading it and update the selection only after explicit approval.
     8. Treat Word and Excel files as local inputs only. Do not retrieve their remote versions automatically, execute files, open macros, or extract archives.
     9. Update `input_selection.json` with local-verification status and results while preserving the recorded selection approval.
     10. Do not invoke `modules.download_ticket_inputs`; automatic direct-file, archive, GitHub-package, Word, and Excel retrieval is disabled for this workflow.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Every included input is present and locally inventoried, and every unexpected file has an explicit decision before inspection.
   - **Completion evidence:** `[manual_placement_confirmation_when_required, local_file_inventory, approved_items_matched, missing_and_unexpected_files_resolved, no_file_content_executed]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/input_selection.json`
   - **Skip reason:** Required when the approved selection is empty and `downloads/` contains no unexpected files.
   - **Failure path:** `stop_and_report_exact_missing_or_unexpected_local_input`

5. **Checklist item:** Synthesize the consolidated ticket context
   - **Checklist item ID:** `synthesize-ticket-context`
   - **Objective:** Produce a durable, provenance-aware context packet that separates business intent, implementation details, evidence, QA assets, metadata, conflicts, and unresolved decisions.
   - **Applicability:** `required`
   - **Applicability rule:** Run after Jira retrieval and local verification are complete or an empty input selection is approved.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[retrieve-jira-business-request_completed, classify-supporting-inputs_completed, securely-acquire-ticket-inputs_completed_or_skipped]`
   - **Required inputs:** `[jira_business_request, approved_input_selection, verified_local_inputs_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, approved_document_readers, authorized_database_metadata_tools_when_applicable]`
   - **Ordered agent actions:**
     1. Read only included, locally verified, supported files required to establish QA context. Never read excluded, deferred, unclear, missing, unexpected, or unverified files.
     2. Update `ticket_context.md` with separate sections for the Jira requirement, technical implementation specification, developer unit-test evidence, QA package inventory, and authorized database metadata when used.
     3. Record provenance for important facts by naming the source role and source artifact.
     4. List unresolved questions, contradictions, assumptions requiring approval, missing technical values, unsupported or unreadable local formats, and references that were not supplied locally.
     5. Do not silently resolve conflicting sources. Identify the conflict and explain its impact on QA scope or execution targets.
     6. Do not invent remote file contents, extracted Word or Excel content, authentication profiles, repositories, package paths, environments, servers, databases, schemas, tables, tokens, or expected outcomes.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Consolidated ticket context is complete enough for an authorized user to approve or reject the interpreted scope.
   - **Completion evidence:** `[role_separated_context, source_provenance, contradictions_listed, unresolved_questions_listed]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/ticket_context.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_context_clarification`

6. **Checklist item:** Obtain ticket-context approval
   - **Checklist item ID:** `approve-ticket-context`
   - **Objective:** Confirm the interpreted requirement and all action-critical execution targets before executable database validation is prepared.
   - **Applicability:** `required`
   - **Applicability rule:** Run after the consolidated context reaches its review checkpoint.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[synthesize-ticket-context_completed]`
   - **Required inputs:** `[ticket_context, unresolved_questions, identified_conflicts, proposed_qa_scope]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[user_conversation, repository_filesystem]`
   - **Ordered agent actions:**
     1. Ensure `ticket_context.md` contains the complete context packet, source status, unresolved facts, proposed QA scope, and excluded or blocked checks.
     2. Present a compact summary and ask exactly `Approve context.`
     3. Do not treat silence, input-selection approval, earlier ticket approval, or artifact existence as context approval.
     4. Record the decision, timestamp, checkpoint, approver identity or role, detailed approved scope, and notes in the approval log.
     5. If rejected or conditionally approved, update the context packet and repeat this checkpoint before proceeding.
   - **Human approval required:** `true`
   - **Human approver role:** `authorized_qa_or_project_representative`
   - **Expected checkpoint:** The consolidated context and action-critical QA scope are explicitly approved.
   - **Completion evidence:** `[explicit_context_decision, context_approval_log_entry]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/approvals/approval_log.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_until_context_is_explicitly_approved`

7. **Checklist item:** Prepare the QA plan
   - **Checklist item ID:** `prepare-qa-plan`
   - **Objective:** Translate the approved context into an ordered, evidence-oriented validation plan.
   - **Applicability:** `required`
   - **Applicability rule:** Run only after explicit context approval.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[approve-ticket-context_completed]`
   - **Required inputs:** `[approved_ticket_context, approved_qa_scope, approved_environment_and_objects]`
   - **Required Agent Skill:** `qa-test-planner`
   - **Permitted tools or systems:** `[repository_filesystem, authorized_metadata_tools_when_required]`
   - **Ordered agent actions:**
     1. Resolve the exact Agent Skill key `qa-test-planner`.
     2. Confirm that `skills/agent_skills/qa-test-planner/` exists and that its folder name exactly matches the required skill key.
     3. Read `skills/agent_skills/qa-test-planner/SKILL.md` completely, confirm that its metadata name exactly matches `qa-test-planner`, and read only the supporting reference files that `SKILL.md` requires for this planning task.
     4. Provide the skill with the approved ticket context, approved QA scope, approved environments, and approved source and target objects.
     5. Use the skill only for QA planning. The skill must not execute or prepare SQL, call Jira, databases, GitHub, or other live systems, bypass workflow approval gates, approve its own output, or invent profiles, servers, databases, schemas, tables, expected outcomes, credentials, or approvals. SQL preparation remains in checklist item 8, and database execution remains after the separate execution-approval checkpoint.
     6. Require the skill to define validation objectives and prerequisites and evaluate every category in the following minimum QA coverage matrix:
        - database, schema, and object existence;
        - column names, data types, lengths, precision, scale, and nullability;
        - source and target row counts;
        - null checks;
        - duplicate and uniqueness checks;
        - primary-key and referential-integrity checks;
        - source-to-target mappings;
        - transformations and business rules;
        - aggregate and reconciliation checks;
        - incremental-load behaviour;
        - idempotency and safe rerun behaviour;
        - audit columns, timestamps, and load identifiers;
        - boundary and negative cases;
        - performance checks only when required by authoritative context; and
        - rollback and recovery behaviour.
     7. Require every minimum matrix category to be marked `applicable`, with checks, expected outcomes, and evidence; `not_applicable`, with an authoritative reason; or `blocked`, with the missing or conflicting information.
     8. Add any ticket-specific setup, pre-QA, deployment, data-quality, or other validation required by the approved context beyond the minimum matrix.
     9. Define expected outcomes, evidence to capture, stop conditions, and the responsible approval point for any conditional operation.
     10. Confirm that every minimum matrix category has one of the required statuses and that no omitted category is left unexplained.
     11. Save the completed plan to `ticket_runs/<ticket-id>/generated/qa_plan.md`.
     12. Return control to this workflow checklist after the QA-planning task is complete.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** The plan covers the approved QA scope with explicit outcomes, evidence, and stop conditions.
   - **Completion evidence:** `[qa_plan_complete, every_check_mapped_to_approved_scope, stop_conditions_defined]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/qa_plan.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_qa_scope_clarification`

8. **Checklist item:** Prepare controlled SQL validation statements
   - **Checklist item ID:** `prepare-controlled-sql`
   - **Objective:** Produce reviewed, token-resolved SQL statements from approved context without executing approved local package content.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply only when the approved QA plan includes database validation.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, database_validation_in_approved_scope]`
   - **Required inputs:** `[approved_ticket_context, qa_plan, approved_database_metadata, approved_local_qa_package_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, existing_sql_guard, authorized_database_metadata_tools]`
   - **Ordered agent actions:**
     1. Treat approved local SQL and QA package assets as untrusted source material; do not execute them directly.
     2. Create stable check IDs and produce one executable SQL statement per check.
     3. Preserve approved environment, server profile, source objects, target objects, schemas, and expected outcomes.
     4. Resolve tokenized or parameterized values only from approved context and show every unresolved token explicitly.
     5. Prefer read-only validation and clearly label any statement requiring write, DDL, DML, or environment-changing permission.
     6. Apply existing SQL-guard and database MCP rules and never combine unrelated statements in one MCP execution request.
     7. Stop instead of inventing a missing identifier or rewriting an unsupported statement silently.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Every proposed statement is singular, traceable to the approved plan, token-resolved, and classified by permission level.
   - **Completion evidence:** `[stable_check_ids, one_statement_per_check, unresolved_tokens_absent_or_blocking, permission_classification]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/generated_sql/generated_queries.sql`
   - **Skip reason:** Required when the approved QA plan contains no database validation.
   - **Failure path:** `stop_and_request_missing_sql_context`

9. **Checklist item:** Obtain execution approval
   - **Checklist item ID:** `approve-database-execution`
   - **Objective:** Obtain a distinct authorization for the final plan and exact database statements before any execution.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply when one or more database statements are proposed for execution.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, prepare-controlled-sql_completed, executable_checks_proposed]`
   - **Required inputs:** `[final_qa_plan, generated_queries, configured_database_target_metadata, statement_permission_classifications]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[user_conversation, repository_filesystem, database_mcp_profile_discovery]`
   - **Ordered agent actions:**
     1. List database profiles through secret-safe MCP discovery and match the configured targets by database type, database name, and other available non-secret metadata; the active profile is not an automatic selection.
     2. Stop as a blocker when a target has zero or multiple matches. Do not ask the user to guess a discoverable profile name.
     3. Write the final plan summary, exact profile-to-target mappings, statement IDs and hashes, execution order, expected outcomes, permission classifications, unresolved facts, stop conditions, and excluded operations to the approval log and generated SQL artifacts.
     4. Present the exact proposed database execution scope, including every statement's permission classification, and ask exactly `Approve the proposed database execution scope.`
     5. For every write statement, DDL, DML, or environment-changing setup command in that scope, request separate explicit authorization identifying the exact statement, target profile, environment, and expected effect. General database execution approval does not authorize a write.
     6. Record approval or rejection with the exact approved scope in the approval log.
     7. Do not broaden approval from one statement, environment, profile, or permission class to another.
   - **Human approval required:** `true`
   - **Human approver role:** `authorized_database_or_qa_representative`
   - **Expected checkpoint:** Exact statements and execution boundaries have explicit recorded approval.
   - **Completion evidence:** `[explicit_execution_decision, exact_statement_scope_recorded, write_authorization_recorded_when_applicable]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/approvals/approval_log.md`
   - **Skip reason:** Required when no database statement will be executed.
   - **Failure path:** `stop_until_execution_is_explicitly_approved`

10. **Checklist item:** Execute approved checks under MCP control
   - **Checklist item ID:** `execute-approved-checks`
   - **Objective:** Execute only approved statements through the database MCP and capture normalized, safe evidence.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply only after the execution-approval checkpoint is completed for at least one exact statement.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[approve-database-execution_completed, approved_database_profile_available, sql_guard_available]`
   - **Required inputs:** `[approved_statements, approved_execution_order, approved_profile, approved_environment, expected_outcomes]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[existing_database_mcp, existing_sql_guard, repository_filesystem]`
   - **Ordered agent actions:**
     1. Switch only to a profile and target included in the recorded execution approval, satisfying any database MCP confirmation contract.
     2. Validate the connection after switching and confirm its safe database metadata matches the approved mapping.
     3. Confirm the statement ID, hash, and permission class still match the approved scope.
     4. For every approved statement, call the database MCP query tool with the exact approved `connection_profile`; do not rely on profile state left by an earlier tool call or process.
     5. Execute exactly one approved statement per database MCP request. The same request must bind and connection-test the named profile before delegating SQL.
     6. Require the MCP result to prove `requested_profile`, `resolved_profile`, `db_type`, `database`, `schema` or `role` when applicable, `statement_hash`, `statement_classification`, and `execution_status`.
     7. Capture the check ID, exact normalized statement, result, row count, duration, status, and secret-safe error information.
     8. Compare the result with its approved expected outcome without changing the query automatically.
     9. Stop on missing or unknown profile, profile-binding or connection failure, policy rejection, target mismatch, changed statement hash, unresolved token, unexpected write behavior, contradiction, or unapproved statement. Do not execute the statement through another path.
     10. Do not read `MCP/.env`, invoke database code through a shell or direct Python process, create a temporary execution helper, automatically retry a destructive action, or execute arbitrary SQL from approved local packages.
     11. Record skipped, blocked, and failed checks explicitly instead of presenting them as successful.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Every attempted database check was approved, individually executed, and normalized into ticket evidence.
   - **Completion evidence:** `[mcp_execution_records, statement_result_mapping, stop_conditions_respected]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json`
   - **Skip reason:** Required when execution was not proposed, not approved, rejected, or blocked.
   - **Failure path:** `stop_execution_and_report_exact_safe_failure`

11. **Checklist item:** Obtain report-export approval
   - **Checklist item ID:** `approve-report-export`
   - **Objective:** Obtain a distinct authorization for the exact final report scope before creating any HTML, Excel, or other final report.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply only when the approved QA plan requires a final report.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, execution_state_known, final_report_required]`
   - **Required inputs:** `[approved_qa_plan, ticket_artifact_inventory, execution_results_when_applicable, proposed_report_scope]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[user_conversation, repository_filesystem]`
   - **Ordered agent actions:**
     1. Confirm that the approved QA plan requires a final report. If it does not, create no report and record the item as skipped with the reason.
     2. Prepare and present the exact proposed report format, destination path, evidence or data to include, whether sensitive information is present, and required redactions.
     3. Ask exactly `Approve the proposed report export.`
     4. Treat silence as no decision. Silence is not approval; context approval, input-selection approval, SQL execution approval, database write approval, and profile-switch approval are not report-export approval.
     5. Record the explicit approval or rejection, approver identity, decision time, exact approved scope, and required redactions in `ticket_runs/<ticket-id>/generated/approvals/approval_log.md` without overwriting prior decisions.
     6. Rejection prevents report creation. An unresolved, partial, changed, or broader report proposal remains unapproved and must not be generated.
     7. Do not create a report in this checklist item; return the recorded decision to the finalization item.
   - **Human approval required:** `true`
   - **Human approver role:** `authorized_qa_or_project_representative`
   - **Expected checkpoint:** The exact report format, destination, evidence scope, sensitivity status, and redactions have an explicit recorded decision.
   - **Completion evidence:** `[explicit_report_export_decision, exact_report_scope_recorded, required_redactions_recorded]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/approvals/approval_log.md`
   - **Skip reason:** Required when the approved QA plan does not require a final report.
   - **Failure path:** `stop_report_creation_until_explicitly_approved`

12. **Checklist item:** Finalize QA evidence and reports
   - **Checklist item ID:** `finalize-qa-evidence`
   - **Objective:** Produce a clear ticket-scoped QA package that distinguishes retrieved, inferred, approved, executed, skipped, blocked, and unresolved work.
   - **Applicability:** `required`
   - **Applicability rule:** Run after planned execution is completed, skipped, rejected, or blocked.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, execution_state_known, approve-report-export_completed_or_skipped]`
   - **Required inputs:** `[ticket_context, input_selection, qa_plan, generated_sql_when_applicable, approval_history, execution_results_when_applicable, report_export_approval_when_applicable]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, existing_supported_report_exporters]`
   - **Ordered agent actions:**
     1. Confirm the ticket package contains the context, QA plan, generated SQL when applicable, approval history, and normalized execution results when applicable.
     2. Reference approved locally verified source inputs and recorded safe metadata without altering the original source files.
     3. Update safe root-level logs without storing credentials, signed URLs, sensitive headers, or raw authentication failures.
     4. Generate the approved HTML, Excel, or other final report only when the approved QA plan requires it and the report-export approval exactly matches its format, destination, evidence scope, sensitivity status, and redactions. Place it only under the approved `output/<ticket-id>/` path.
     5. State clearly what was retrieved, inferred, approved, executed, skipped, blocked, and unresolved.
     6. Do not claim completion for a blocked check or execution that did not occur.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Ticket evidence is complete, traceable, safely stored, and honest about incomplete work.
   - **Completion evidence:** `[ticket_artifact_inventory, final_status_summary, source_hash_references, report_export_approval_when_applicable, report_paths_when_applicable]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_report_incomplete_evidence_package`

## Error Handling / Fallbacks

- **Preflight blocker:** Stop before workspace initialization and create no ticket runtime artifacts. Authentication, configuration, connector, dependency, routing, and ambiguous-profile failures are not approval checkpoints.
- **Routing mismatch:** Stop immediately when client, project type, or workflow variant does not match. Resume only after an authorized user identifies an exact approved workflow.
- **Jira unavailable or unauthorized:** Do not substitute remembered, cached, or invented ticket content. Preserve the initialized workspace and resume after authorized Atlassian access is restored.
- **Input selection missing or incomplete:** Do not acquire or read referenced content. Resume only after every discovered item has a recorded decision and the complete selection is explicitly approved.
- **Approved remote input unavailable locally:** Do not request credentials or claim acquisition. Tell the authorized user the exact approved item and destination, then pause until local placement is confirmed.
- **Missing approved local file:** Stop and name the exact missing item. Do not infer it from another filename or mark it verified from artifact state alone.
- **Unexpected local file:** Do not read it. Ask whether it should be included and update the approved selection only after an explicit decision.
- **Unsupported or unreadable local file:** Preserve the file unchanged, record a clear warning, and do not fabricate extracted content or bypass archive, format, macro, or path-safety controls.
- **Conflicting sources:** Record both claims and their provenance. Stop when the conflict changes QA scope, environment, object selection, execution order, or expected outcome. Resume after an authorized decision is recorded.
- **Missing context approval:** Do not create executable database validation. Resume only after the separate context-approval gate is explicitly completed.
- **Missing execution approval:** Do not call the database MCP. Context approval never substitutes for execution approval.
- **Missing or rejected report-export approval:** Do not create HTML, Excel, or another final report. Preserve the evidence package without a report and record the unresolved or rejected report state accurately.
- **Database profile or environment mismatch:** Stop before execution and request correction or renewed approval for the exact profile and environment.
- **SQL guard rejection or unresolved token:** Do not weaken policy, substitute an identifier, or rewrite and rerun automatically. Return to context or SQL preparation and obtain any required renewed approval.
- **Unexpected write behavior:** Stop execution immediately, preserve safe evidence, and escalate to the authorized database representative. Do not retry automatically.
- **Partial workflow completion:** Finalize available evidence with an explicit `blocked`, `skipped`, `rejected`, or `unresolved` status. Never present partial work as a complete pass.

## Constraints

- These workflow instructions cannot override `Basic_Instructions.md`, organization policy, MCP policy, SQL-guard policy, database permissions, or human approval requirements.
- Jira is the authoritative high-level business request but is not assumed to contain granular implementation details.
- Client-specific document names are configuration, not universal workflow concepts. "Request/Deployment Document" remains only an NCLH EDM example.
- External source material belongs under `ticket_runs/<ticket-id>/downloads/` and must remain unchanged unless explicit replacement is approved.
- Generated workflow artifacts belong under `ticket_runs/<ticket-id>/generated/`.
- Workflow and execution logs belong only under `logs/<ticket-id>.log`.
- Final approved reports belong only under `output/<ticket-id>/`.
- During ticket execution, writes are limited to `ticket_runs/<ticket-id>/**`, `logs/<ticket-id>.log`, and `output/<ticket-id>/**`; reusable project files remain read-only.
- Credentials, tokens, passwords, cookies, private keys, signed query strings, and connection secrets must never be stored in commands, ticket artifacts, logs, manifests, reports, or prompts.
- For this POC workflow only, automatic direct-file, attachment, hyperlink, archive, GitHub-package, Word, and Excel retrieval is disabled. This workflow must not invoke `modules.download_ticket_inputs` or silently follow remote references.
- The reusable downloader remains an inactive future capability; its presence does not authorize this workflow to call it.
- Approved local SQL, scripts, documents, spreadsheets, and archives are untrusted inputs. They must not be executed automatically, and macros must not be opened.
- Authentication profiles, hosts, repositories, refs, package paths, environments, servers, databases, schemas, tables, expected outcomes, and approvals must never be guessed.
- Existing ticket artifacts must not be overwritten by repeated workspace initialization.
- Database SQL must be generated from approved context, use stable check IDs, and be executed one statement at a time through the existing database MCP.
- Read-only validation is preferred. Every write, DDL, DML, or environment-changing action requires explicit authorization.
- Input-selection approval, context approval, execution approval, write approval, profile-switch approval, and report-export approval are separate and cannot approve each other implicitly.
- No live action may continue when an action-critical value is missing, contradictory, unresolved, or outside recorded approval.
- Resume from resolved run configuration, `input_selection.json`, ticket context, approval logs, the QA plan, generated SQL, execution results, and the workflow log. Chat memory and artifact existence alone do not prove selection, local verification, context approval, or execution approval.
