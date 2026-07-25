---
document_type: "qa_workflow"
client_name: "ruhan"
project_type: "poc"
workflow_variant: null
created_by: "ruhannaik0120"
created_on: "2026-07-25"
last_edited_by: "ruhannaik0120"
last_edited_on: "2026-07-25"
version: "1.0"
workflow_owner: "ruhannaik0120"
approved_by: "ruhannaik0120"
approved_on: "2026-07-25"
---

# Jira-Driven QA Automation POC Workflow

## Purpose

This workflow coordinates QA preparation, controlled database validation, and evidence generation for an authorized Jira ticket routed to the `ruhan` demonstration client and `poc` project type. It starts when the user supplies a Jira ticket key and remains valid across tickets whose document names, formats, environments, and validation details differ.

The workflow treats Jira as the high-level business request and uses supporting material to establish the technical details needed for QA. It does not assume that Jira contains server names, schemas, tables, package paths, execution order, or other implementation details. Those values must come from authorized sources and must be approved before use.

The procedure is client-agnostic in how it classifies inputs. It uses the permanent source roles defined below instead of relying on one client's filename:

- **Jira business request:** the high-level issue, product change, or requested work, usually created by a product owner.
- **Technical implementation specification:** the granular implementation and QA instructions completed by the developer after requirement gathering. Its client-specific name is configurable. "Request/Deployment Document" is an NCLH EDM example only; other clients may use Technical Design Document, Deployment Specification, Implementation Document, Change Specification, or another approved name.
- **Developer unit-test evidence:** developer-produced test results or evidence in an approved format such as DOCX, XLSX, PDF, CSV, screenshots, or another declared format.
- **QA package:** QA-specific tokenized or parameterized assets. It may contain SQL validation scripts, DDL, DML, setup queries, pre-QA queries, post-QA checks, reconciliation queries, data-validation queries, or ETL/data-pipeline SQL assets. Downloaded package content is source material and is never executed automatically.

## Scope

This workflow applies only when authoritative context establishes:

- `client_name` as `ruhan`;
- `project_type` as `poc`, normally from the Jira title or other authoritative ticket metadata;
- no additional `workflow_variant`; and
- the supplied Jira ticket key as the ticket-run identifier.

The workflow covers:

- automatic ticket-workspace initialization;
- authorized Jira retrieval;
- discovery, role classification, and secure acquisition of declared supporting inputs;
- consolidated context synthesis and conflict handling;
- a separate context-approval checkpoint;
- QA planning and conditional SQL preparation;
- a separate execution-approval checkpoint;
- controlled one-statement-at-a-time database MCP execution when applicable and approved; and
- final evidence and report preparation using existing supported project capabilities.

This workflow does not assume that every ticket includes external documents, a GitHub package, SQL, database validation, DDL, DML, HTML reports, or Excel reports. Conditional checklist items must be skipped with a recorded reason when authoritative context proves they do not apply.

This workflow is not applicable when the client, project type, or workflow variant does not match its metadata exactly. It is also not applicable to unsupported ticket categories, requests lacking an authoritative Jira key, or work that requires a different approved workflow. In those cases, the agent must stop and request clarification from the workflow owner or an authorized user.

## Prerequisites

- The user must provide a Jira ticket key. The agent must not infer or reuse a ticket key from an unrelated run.
- The agent must have access to the repository and its existing Python environment so it can run the ticket initializer and secure downloader modules.
- Jira retrieval must use an authorized Atlassian integration. Missing authorization is blocking and must not be bypassed with guessed or cached ticket content.
- The authoritative client identity and Jira project type must exactly match this workflow's routing metadata.
- Supporting inputs must be declared by Jira, an authorized user, or another approved source. The agent must classify them by role rather than by filename alone.
- Credential-protected documents that cannot be retrieved by the agent must be downloaded by an authorized user and placed under `ticket_runs/<ticket-id>/downloads/`.
- Authentication profiles, allowed hosts, repository names, repository refs, package paths, environments, server names, database names, schemas, tables, and execution targets must come from authorized sources. Missing values are blocking.
- Database execution requires a configured database MCP profile, successful connection validation, applicable SQL-guard acceptance, and explicit execution approval.
- Write operations, DDL, DML, and environment-changing setup require their own explicit authorization. Read-only approval never implies write approval.
- No Agent Skill is mandatory for this workflow. A future approved revision may declare an exact skill key inside the checklist item where that skill is required.

## Steps

The checklist below is the ticket-independent control path for this client and
project type. It initializes a resumable workspace, classifies authoritative
inputs by role, acquires only declared sources, and synthesizes context before
the first approval gate. Planning and any applicable SQL preparation occur
only after that context is approved; a second approval gate controls database
execution, and evidence and reports are produced from recorded results rather
than assumed outcomes. Each ticket records its own status and artifacts under
the paths named by the applicable checklist item.

1. **Checklist item:** Initialize the ticket workspace
   - **Checklist item ID:** `initialize-ticket-workspace`
   - **Objective:** Create the stable ticket-scoped input and generated-artifact structure before retrieving or producing ticket content.
   - **Applicability:** `required`
   - **Applicability rule:** Run once at the beginning of every ticket run and safely repeat when resuming.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[user_supplied_jira_ticket_key]`
   - **Required inputs:** `[jira_ticket_key]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[local_python, modules.init_ticket_run, repository_filesystem]`
   - **Ordered agent actions:**
     1. Validate that the user supplied a Jira ticket key.
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
     1. Retrieve the Jira title, description, acceptance information, attachments, links, and other authorized ticket fields.
     2. Confirm that the ticket metadata routes exactly to `client_name: ruhan`, `project_type: poc`, and no workflow variant.
     3. Record Jira as the high-level business request, not as proof of missing technical details.
     4. Inventory every declared supporting document, attachment, repository reference, package path, and evidence source without following an undeclared location.
     5. Record unavailable or permission-protected sources as unresolved inputs.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Authoritative Jira content and its declared source inventory are available for classification.
   - **Completion evidence:** `[jira_ticket_retrieved, routing_metadata_confirmed, declared_sources_inventoried]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/ticket_context.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_authorized_jira_access_or_routing_clarification`

3. **Checklist item:** Classify and validate supporting input declarations
   - **Checklist item ID:** `classify-supporting-inputs`
   - **Objective:** Map each declared source to a generic workflow role and establish the exact retrieval details required for safe acquisition.
   - **Applicability:** `required`
   - **Applicability rule:** Run for every ticket, including tickets that declare no supporting inputs.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[retrieve-jira-business-request_completed]`
   - **Required inputs:** `[jira_business_request, declared_source_inventory, client_or_project_configuration_when_applicable]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[authorized_atlassian_integration, repository_filesystem, authorized_user_context]`
   - **Ordered agent actions:**
     1. Classify each source as a technical implementation specification, developer unit-test evidence, QA package, or another explicitly approved role.
     2. Use client or project configuration to interpret client-specific document names; never assume one universal title or filename.
     3. For each direct file, establish the declared expected extension, exact allowed host, and named environment-backed authentication profile when required.
     4. For each repository package, establish the exact owner/repository, ref, package path, allowed file extensions, and named environment-backed authentication profile.
     5. Identify missing, contradictory, ambiguous, or permission-protected details and do not guess replacements.
     6. Record that no supporting inputs were declared when authoritative ticket context confirms that result.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Every declared source has an explicit role and complete safe retrieval details, or is recorded as blocked.
   - **Completion evidence:** `[role_based_source_inventory, retrieval_details_validated, unresolved_inputs_recorded]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/ticket_context.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_missing_source_details`

4. **Checklist item:** Acquire declared external inputs securely
   - **Checklist item ID:** `securely-acquire-ticket-inputs`
   - **Objective:** Place validated copies of declared external source material in the ticket downloads directory without exposing credentials or executing content.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply when the classified source inventory contains a retrievable direct file or exact repository package.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[classify-supporting-inputs_completed, complete_retrieval_details_available]`
   - **Required inputs:** `[ticket_id, classified_source_inventory, expected_extensions, exact_allowed_hosts, named_authentication_profiles_when_required]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[local_python, modules.download_ticket_inputs, authorized_network_destinations, repository_filesystem]`
   - **Ordered agent actions:**
     1. Use behavior equivalent to `python -m modules.download_ticket_inputs file ...` for each declared direct file.
     2. Use behavior equivalent to `python -m modules.download_ticket_inputs github-package ...` for each declared exact GitHub repository package.
     3. Pass credentials only through named environment-backed profiles; never place tokens, passwords, cookies, or authentication headers in command-line values or ticket artifacts.
     4. Use the declared expected extension, exact host allowlist, repository, ref, package path, and permitted package extensions.
     5. Do not use overwrite unless an authorized user explicitly approves replacement of the named existing artifact.
     6. Review `ticket_runs/<ticket-id>/generated/download_manifest.json` for successful paths, file types, byte sizes, hashes, and sanitized source information.
     7. Preserve downloaded source files unchanged and never execute downloaded SQL or scripts.
     8. If credential-protected content cannot be accessed, request an authorized user to place it under `downloads/` and then inventory it locally.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Every applicable source is safely stored and represented in the download manifest.
   - **Completion evidence:** `[validated_downloaded_inputs, reviewed_download_manifest, no_downloaded_content_executed]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/download_manifest.json`
   - **Skip reason:** Required when authoritative context confirms that no external input must be acquired.
   - **Failure path:** `stop_and_report_secure_download_blocker`

5. **Checklist item:** Synthesize the consolidated ticket context
   - **Checklist item ID:** `synthesize-ticket-context`
   - **Objective:** Produce a provenance-aware context that separates business intent, implementation details, evidence, QA assets, metadata, conflicts, and unresolved decisions.
   - **Applicability:** `required`
   - **Applicability rule:** Run after Jira retrieval and all applicable input acquisition attempts are complete.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[retrieve-jira-business-request_completed, classify-supporting-inputs_completed, securely-acquire-ticket-inputs_completed_or_skipped]`
   - **Required inputs:** `[jira_business_request, classified_supporting_inputs, download_manifest_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, approved_document_readers, authorized_database_metadata_tools_when_applicable]`
   - **Ordered agent actions:**
     1. Read only the supporting files required to establish QA context.
     2. Update `ticket_context.md` with separate sections for the Jira requirement, technical implementation specification, developer unit-test evidence, QA package inventory, and authorized database metadata when used.
     3. Record provenance for important facts by naming the source role and source artifact.
     4. List unresolved questions, contradictions, assumptions requiring approval, and missing technical values.
     5. Do not silently resolve conflicting sources. Identify the conflict and explain its impact on QA scope or execution targets.
     6. Do not invent authentication profiles, allowed hosts, repositories, refs, package paths, environments, servers, databases, schemas, tables, tokens, or expected outcomes.
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
     1. Present the consolidated context and clearly identify information that was retrieved, inferred, contradictory, or unresolved.
     2. Request explicit approval of the interpreted requirement, environment, server or connection profile, source and target objects, QA scope, package and script selection, and every remaining assumption.
     3. Do not treat silence, earlier ticket approval, or artifact existence as approval.
     4. Record the decision, timestamp, checkpoint, approver identity or role, and notes in the approval log.
     5. If rejected or conditionally approved, update the context and repeat this checkpoint before proceeding.
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
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, authorized_metadata_tools_when_required]`
   - **Ordered agent actions:**
     1. Define validation objectives, prerequisites, approved environments, and approved source and target objects.
     2. Define applicable setup checks, pre-QA checks, transformation or deployment validations, data-quality checks, reconciliation checks, and negative or edge checks.
     3. Include rollback or recovery checks when the approved change has recoverable state.
     4. Define expected outcomes, evidence to capture, stop conditions, and the responsible approval point for any conditional operation.
     5. Distinguish required checks from non-applicable checks and record why an omitted category does not apply.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** The plan covers the approved QA scope with explicit outcomes, evidence, and stop conditions.
   - **Completion evidence:** `[qa_plan_complete, every_check_mapped_to_approved_scope, stop_conditions_defined]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/qa_plan.md`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_qa_scope_clarification`

8. **Checklist item:** Prepare controlled SQL validation statements
   - **Checklist item ID:** `prepare-controlled-sql`
   - **Objective:** Produce reviewed, token-resolved SQL statements from approved context without executing downloaded package content.
   - **Applicability:** `conditional`
   - **Applicability rule:** Apply only when the approved QA plan includes database validation.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, database_validation_in_approved_scope]`
   - **Required inputs:** `[approved_ticket_context, qa_plan, approved_database_metadata, downloaded_qa_package_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, existing_sql_guard, authorized_database_metadata_tools]`
   - **Ordered agent actions:**
     1. Treat downloaded SQL and QA package assets as untrusted source material; do not execute them directly.
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
   - **Required inputs:** `[final_qa_plan, generated_queries, approved_connection_profile, statement_permission_classifications]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[user_conversation, repository_filesystem]`
   - **Ordered agent actions:**
     1. Present the final QA plan, exact statements, statement order, approved profile and environment, expected outcomes, and stop conditions.
     2. Request explicit database-execution approval separately from context approval.
     3. Request separate explicit authorization for every write statement, DDL, DML, or environment-changing setup command.
     4. Record approval or rejection with the exact approved scope in the approval log.
     5. Do not broaden approval from one statement, environment, profile, or permission class to another.
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
   - **Entry conditions:** `[approve-database-execution_completed, approved_database_profile_available, connection_validated, sql_guard_available]`
   - **Required inputs:** `[approved_statements, approved_execution_order, approved_profile, approved_environment, expected_outcomes]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[existing_database_mcp, existing_sql_guard, repository_filesystem]`
   - **Ordered agent actions:**
     1. Confirm the active profile and environment match the recorded execution approval.
     2. Execute exactly one approved statement per database MCP request.
     3. Capture the check ID, exact normalized statement, result, row count, duration, status, and secret-safe error information.
     4. Compare the result with its approved expected outcome without changing the query automatically.
     5. Stop on policy rejection, profile or environment mismatch, unresolved token, unexpected write behavior, contradiction, or unapproved statement.
     6. Do not automatically retry a destructive action and do not execute arbitrary SQL from downloaded packages.
     7. Record skipped, blocked, and failed checks explicitly instead of presenting them as successful.
   - **Human approval required:** `true`
   - **Human approver role:** `authorized_database_or_qa_representative`
   - **Expected checkpoint:** Every attempted database check was approved, individually executed, and normalized into ticket evidence.
   - **Completion evidence:** `[mcp_execution_records, statement_result_mapping, stop_conditions_respected]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json`
   - **Skip reason:** Required when execution was not proposed, not approved, rejected, or blocked.
   - **Failure path:** `stop_execution_and_report_exact_safe_failure`

11. **Checklist item:** Finalize QA evidence and reports
   - **Checklist item ID:** `finalize-qa-evidence`
   - **Objective:** Produce a clear ticket-scoped QA package that distinguishes retrieved, inferred, approved, executed, skipped, blocked, and unresolved work.
   - **Applicability:** `required`
   - **Applicability rule:** Run after planned execution is completed, skipped, rejected, or blocked.
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[prepare-qa-plan_completed, execution_state_known]`
   - **Required inputs:** `[ticket_context, qa_plan, generated_sql_when_applicable, approval_history, execution_results_when_applicable, download_manifest_when_present]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[repository_filesystem, existing_supported_report_exporters]`
   - **Ordered agent actions:**
     1. Confirm the ticket package contains the context, QA plan, generated SQL when applicable, approval history, and normalized execution results when applicable.
     2. Reference downloaded source inputs and manifest hashes without altering the original source files.
     3. Update safe root-level logs without storing credentials, signed URLs, sensitive headers, or raw authentication failures.
     4. Generate existing supported HTML or Excel report exports only when required by the approved QA plan and place final reports under `output/<ticket-id>/`.
     5. State clearly what was retrieved, inferred, approved, executed, skipped, blocked, and unresolved.
     6. Do not claim completion for a blocked check or execution that did not occur.
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** Ticket evidence is complete, traceable, safely stored, and honest about incomplete work.
   - **Completion evidence:** `[ticket_artifact_inventory, final_status_summary, source_hash_references, report_paths_when_applicable]`
   - **Generated or updated artifact:** `ticket_runs/<ticket-id>/generated/`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_report_incomplete_evidence_package`

## Error Handling / Fallbacks

- **Routing mismatch:** Stop immediately when client, project type, or workflow variant does not match. Resume only after an authorized user identifies an exact approved workflow.
- **Jira unavailable or unauthorized:** Do not substitute remembered, cached, or invented ticket content. Preserve the initialized workspace and resume after authorized Atlassian access is restored.
- **Credential-protected input unavailable:** Do not request credentials. Ask an authorized user to download the source through their own approved session and place it in the ticket `downloads/` directory.
- **Missing retrieval detail:** Stop when an allowed host, expected extension, authentication profile, repository, ref, or exact package path is missing. Resume only after an authorized source supplies the exact value.
- **Unsafe or invalid download:** Preserve any prior source files, record the safe downloader error, and do not bypass host, format, size, archive, or overwrite controls.
- **Conflicting sources:** Record both claims and their provenance. Stop when the conflict changes QA scope, environment, object selection, execution order, or expected outcome. Resume after an authorized decision is recorded.
- **Missing context approval:** Do not create executable database validation. Resume only after the first approval gate is explicitly completed.
- **Missing execution approval:** Do not call the database MCP. Context approval never substitutes for execution approval.
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
- Credentials, tokens, passwords, cookies, private keys, signed query strings, and connection secrets must never be stored in commands, ticket artifacts, logs, manifests, reports, or prompts.
- The workflow must use `modules.download_ticket_inputs` for declared direct-file and GitHub-package acquisition instead of implementing an alternate downloader.
- Downloaded SQL, scripts, documents, and archives are untrusted inputs. They must not be executed automatically.
- Authentication profiles, hosts, repositories, refs, package paths, environments, servers, databases, schemas, tables, expected outcomes, and approvals must never be guessed.
- Existing ticket artifacts must not be overwritten by repeated workspace initialization.
- Database SQL must be generated from approved context, use stable check IDs, and be executed one statement at a time through the existing database MCP.
- Read-only validation is preferred. Every write, DDL, DML, or environment-changing action requires explicit authorization.
- The context-approval and execution-approval checkpoints are separate and cannot approve each other implicitly.
- No live action may continue when an action-critical value is missing, contradictory, unresolved, or outside recorded approval.
