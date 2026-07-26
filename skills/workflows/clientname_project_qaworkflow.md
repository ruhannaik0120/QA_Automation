---
document_type: "qa_workflow_template"
client_name: "<client-name>"
project_type: "<project-type>"
workflow_variant: null
created_by: "<creator-name-or-id>"
created_on: "<yyyy-mm-dd>"
last_edited_by: "<editor-name-or-id>"
last_edited_on: "<yyyy-mm-dd>"
version: "<version>"
workflow_owner: "<workflow-owner-name-or-id>"
approved_by: null
approved_on: null
---

# QA Workflow Template

## Purpose

- State the permanent business purpose of this client/project workflow and the outcome it is intended to coordinate.
- Explain why this workflow exists and how it differs from other workflows that may belong to the same client.
- Give the AI enough detail to understand the workflow's objective without relying on one example ticket.
- Define terms that could otherwise have more than one meaning, especially client-specific language and project-type terminology.
- Do not include ticket-specific requirements, values, decisions, or artifacts. This section must remain valid across all supported tickets routed to this workflow.

## Scope

- Identify the client represented by `client_name`, the supported project type represented by `project_type`, and the optional additional routing condition represented by `workflow_variant`.
- Describe the ticket categories, title indicators, requests, and boundaries that make this workflow applicable.
- Explain why each routing condition is necessary so the AI can distinguish this workflow from other workflows for the same client.
- Be precise enough that applicability can be decided from authoritative metadata without similarity guessing.
- State explicit exclusions and unsupported conditions. Do not describe the contents or expected outcome of one specific ticket.

Completed workflow filenames are based only on `client_name`, `project_type`, and the optional `workflow_variant`:

```text
skills/workflows/<client-name>_<project-type>_qaworkflow.md
skills/workflows/<client-name>_<project-type>_<workflow-variant>_qaworkflow.md
```

Examples:

```text
skills/workflows/nclh_edm_qaworkflow.md
skills/workflows/nclh_edm_reconciliation_qaworkflow.md
```

Other metadata fields must not affect the filename. For a completed workflow, change `document_type` to `"qa_workflow"`; `client_name` and `project_type` are mandatory, `workflow_variant` is optional and defaults to `null`, and other unavailable metadata may remain `null`. Approval fields must remain `null` until real approval is provided.

## Prerequisites

- The global AI-orchestrated preflight in `Basic_Instructions.md` must succeed before workflow step 1 initializes a ticket workspace. Preflight blockers are not approval checkpoints and must create no ticket runtime artifacts.
- List the permanent information, authorization, access, source material, environment readiness, and human roles required before this workflow can begin.
- Explain why every prerequisite is needed and how the AI can verify readiness without exposing credentials or inventing missing context.
- Specify required detail such as authoritative source, acceptable format, responsible role, and readiness condition.
- Make blocking and non-blocking prerequisites unambiguous, including what the AI must do when a prerequisite is absent.
- Define reusable prerequisites only; ticket-specific inputs belong under `ticket_runs/<ticket-id>/downloads/` or `ticket_runs/<ticket-id>/generated/` as appropriate.
- Declare an Agent Skill directly inside the checklist item where it is required, not in the YAML metadata.

## Steps

- Define the permanent ordered checklist items for this client/project workflow. Add, remove, or repeat the skeleton below until the complete workflow is represented.
- Every workflow step is a checklist item. Explain why each item exists and how it advances the workflow, with enough detail for consistent execution across supported tickets.
- Classify each checklist item as `required`, `conditional`, `optional`, or `not_applicable` using its **Applicability** value.
- At runtime, **Checklist status** must be one of `not_started`, `in_progress`, `completed`, `skipped`, or `blocked`.
- Make ordering, dependencies, decision rules, permissions, approvals, checkpoints, completion evidence, artifacts, and failure routing explicit.
- Do not assume a particular tool, database, protocol, design platform, export format, or previous proof-of-concept process unless this client/project workflow permanently requires it.
- Preserve this order when applicable: successful global preflight; workspace initialization; direct Jira retrieval and configured source acquisition; durable context and context approval; QA planning; safe database-profile discovery; presentation and approval of exact read-only SQL scope and profile mappings; approved profile switching and connection validation; one approved statement per MCP call; and final evidence, reports, and logs.
- Use only the context and database-execution approval checkpoints for normal read-only work. Configuration, authentication, connector, dependency, routing, and profile-discovery failures are blockers; DDL, DML, and environment changes require separate explicit authorization.
- Resume from routing configuration and durable ticket artifacts rather than chat history, and keep normal ticket writes inside the configured ticket, log, and output paths.
- Do not place ticket-specific content in checklist definitions. Runtime ticket information and generated outputs belong in the ticket workspace.

Apply these checklist rules:

- A checklist item cannot be marked `completed` until its expected checkpoint and completion evidence are satisfied.
- A `conditional` or `optional` item may be marked `skipped` only when its applicability rule permits it.
- Every skipped item must record a skip reason.
- If applicability cannot be safely determined, mark the item `blocked`.
- Missing, `null`, or unresolved values must never be treated as permission to perform an action.
- If an action-critical value is missing or contradictory, mark the item `blocked` and follow its failure path.

1. **Checklist item:** `<stable-step-name>`
   - **Checklist item ID:** `<stable-lowercase-hyphenated-id>`
   - **Objective:** `<permanent-outcome-this-item-must-achieve>`
   - **Applicability:** `conditional`
   - **Applicability rule:** `null`
   - **Checklist status:** `not_started`
   - **Entry conditions:** `[]`
   - **Required inputs:** `[]`
   - **Required Agent Skill:** `null`
   - **Permitted tools or systems:** `[]`
   - **Ordered agent actions:**
     1. `<first-unambiguous-action>`
     2. `<next-unambiguous-action>`
     3. `<additional-actions-as-required>`
   - **Human approval required:** `false`
   - **Human approver role:** `null`
   - **Expected checkpoint:** `null`
   - **Completion evidence:** `[]`
   - **Generated or updated artifact:** `null`
   - **Skip reason:** `null`
   - **Failure path:** `stop_and_request_clarification`

These defaults are intentionally safe:

- applicability defaults to `conditional`;
- checklist status defaults to `not_started`;
- list values default to `[]`;
- optional values default to `null`;
- Agent Skill defaults to `null`;
- human approval defaults to `false`; and
- failure handling defaults to `stop_and_request_clarification`.

A completed workflow must replace every action-critical placeholder or `null` value required for execution.

When a checklist item requires an Agent Skill:

- **Required Agent Skill** must contain the exact skill identifier;
- it resolves to `skills/agent_skills/<skill-name>/SKILL.md`;
- the value must match the skill folder name and the `name` field in `SKILL.md`;
- the skill applies only to that checklist item;
- control returns to the workflow checklist when the skill finishes; and
- a missing or conflicting required skill makes the checklist item `blocked`.

## Error Handling / Fallbacks

- Define permanent failure categories, unsupported conditions, retry limits, escalation paths, and safe stopping behavior for this workflow.
- Explain why each fallback exists and what information the AI must preserve or report when using it.
- Provide enough detail to distinguish recoverable errors, approval blockers, missing prerequisites, routing mismatches, and conditions requiring human ownership.
- Name the responsible role and the exact condition for resuming; do not use vague directions such as "handle appropriately" or "continue if possible."
- Keep fallback rules reusable across the client/project workflow. Do not include an actual ticket failure, approval decision, execution result, or evidence record.

## Constraints

- State all permanent client/project restrictions governing data handling, folder ownership, tool use, system access, approvals, generated artifacts, retention, and prohibited actions.
- Explain why each constraint exists so the AI can apply it correctly when multiple rules interact.
- Specify whether each constraint is mandatory, conditional, or advisory and define every condition precisely.
- Resolve potentially ambiguous terms and identify which authoritative role decides any permitted exception.
- Do not repeat one ticket's requirements or hardcode ticket context, QA plans, generated instructions, approvals, execution results, evidence, or reports.
- Keep external ticket documents under `ticket_runs/<ticket-id>/downloads/` and ticket-generated information under `ticket_runs/<ticket-id>/generated/`.
- Do not allow this workflow or a referenced Agent Skill to override permanent project-wide rules in `Basic_Instructions.md`.
