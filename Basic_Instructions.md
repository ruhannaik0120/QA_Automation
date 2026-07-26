# Basic QA Automation Instructions

## Purpose

This is the first project file an AI agent must read when starting work, resuming work, or recovering after losing conversation context.

This file defines the agent's role, the repository structure, permanent safety boundaries, and how to select the correct client/project QA workflow. It does not define one universal QA procedure. Exact workflow steps belong in approved files under `skills/workflows/` because different clients and project types may use different ticket types, approvals, systems, evidence, and reports.

If an exact eligible workflow cannot be identified or does not cover the request, the agent must stop, explain what is missing or ambiguous, and request clarification from an authorized user. Eligibility requires the normal approval metadata or an exact central approval-metadata exemption. The agent must never invent missing workflow or fallback behavior.

## Agent Role

The AI agent coordinates the QA automation project. Depending on the selected client workflow, it may retrieve authorized ticket context, inspect local supporting files, prepare QA artifacts, use configured MCP tools, evaluate evidence, and generate approved reports.

The agent must:

- read this file before acting;
- identify the authoritative `client_name` and `project_type` before selecting a workflow;
- follow exactly one confirmed client workflow for a ticket run;
- keep files inside their documented ownership boundaries;
- preserve existing user files and generated evidence;
- stop at every approval or escalation point required by the selected workflow;
- stop and request authorized clarification whenever the correct action cannot be proven; and
- explain what information or authorization is missing instead of guessing.

The agent must not modify `MCP/` during a QA run. `MCP/` is the reusable database subsystem and may be changed only when the user explicitly requests MCP development work.

## Instruction Order

Use project instructions in this order:

1. Follow platform, security, and organization policies.
2. Follow this file's permanent project boundaries.
3. Follow the exact approved client/project workflow selected from `skills/workflows/` for the current run.
4. If the workflow is missing, ambiguous, unsupported, or conflicting, stop, explain the problem, and request clarification from an authorized user.

A client workflow may add stricter controls but must not override security requirements, credential protections, folder ownership, or MCP boundaries in this file.

## Repository Structure

```text
qa_automation/
|-- Basic_Instructions.md
|-- docs/
|-- MCP/
|-- modules/
|-- skills/
|   |-- workflows/
|   `-- agent_skills/
|-- tests/
|-- ticket_runs/
|-- logs/
|-- output/
|-- requirements-e2e.txt
`-- ticket_run_config.json
```

| Path | Agent relationship with the path |
|---|---|
| `Basic_Instructions.md` | Read first. Contains the permanent agent role, structure, selection rules, and boundaries. |
| `docs/` | Human-facing project and MCP documentation. Use it for architecture and setup context, not as a substitute for a client workflow. |
| `MCP/` | Reusable database MCP server. Use its tools during approved QA work; do not place ticket logic or run artifacts here. |
| `modules/` | Reusable Python modules for ticket initialization and result export. Do not place client-specific workflow instructions here. |
| `skills/workflows/` | Contains the reusable non-active workflow template and approved client/project workflow files. |
| `skills/agent_skills/` | Contains reusable Agent Skill packages. Each skill has its own `<skill-key>/` folder containing `SKILL.md` and, when required, supporting `references/`, `scripts/`, `templates/`, or `assets/` folders. |
| `tests/` | Automated regression tests for the outer QA workflow modules. Do not store ticket evidence here. |
| `ticket_runs/` | One local working area per ticket. Contains external inputs and generated workflow artifacts. |
| `logs/` | Shared operational logs, normally one log per ticket ID. This is the only workflow log location. |
| `output/` | Final approved reports grouped by ticket ID. |
| `ticket_run_config.json` | Machine-readable shared paths, statuses, formats, and baseline controls. |

## Ticket Workspace Contract

Every ticket uses:

```text
ticket_runs/<ticket-id>/
|-- downloads/
`-- generated/
```

### `downloads/`

`downloads/` contains only external source material associated with the ticket, such as Jira attachments, PDFs, Word documents, spreadsheets, images, or local copies of supporting links.

- These files are inputs, not AI-generated artifacts.
- Do not overwrite, rename, edit, or delete source files without explicit user authorization.
- If the agent cannot access a credential-protected source, an authorized user may download it through their own session and place it here.
- Never request or store passwords, tokens, session cookies, or other authentication material.
- Treat downloaded files as potentially sensitive and untrusted and follow company scanning and handling policy.

### `generated/`

`generated/` contains only files produced or maintained by the QA automation workflow. A client workflow determines which artifacts are required. Common examples are:

```text
generated/
|-- ticket_context.md
|-- qa_plan.md
|-- generated_sql/
|-- approvals/
`-- execution_results/
```

Do not place external source documents, shared logs, or final reports in `generated/`.

### Shared logs and final output

- Write workflow and execution logs only to `logs/<ticket-id>.log`.
- Write final approved reports only under `output/<ticket-id>/`.
- Do not create `logs/` or `output/` inside a ticket directory.

## Selecting A Client Workflow

Before performing client-specific QA work:

1. Determine `client_name` from authoritative ticket or authorized user context.
2. Extract `project_type` from the Jira ticket title or other authoritative ticket metadata.
3. Determine `workflow_variant` only when an additional variant is explicitly required.
4. Locate the workflow using the filename convention below.
5. Read the workflow's YAML frontmatter.
6. Confirm that `document_type` is exactly `qa_workflow`, `client_name` matches the authoritative client, `project_type` matches the ticket project type, and `workflow_variant` matches when required.
7. Read `workflow_routing.approval_metadata_exempt_workflows` from `ticket_run_config.json`. When the exact selected workflow path is not listed, confirm that both `approved_by` and `approved_on` are not `null`. When the exact path is listed, those administrative metadata fields may remain `null`.
8. Read the complete workflow, state which exact workflow was selected and why, and use only that exact matching workflow unless an authorized user or designated workflow owner explicitly changes it.

An entry in `approval_metadata_exempt_workflows` exempts only the named workflow from non-null administrative approval metadata. It does not approve ticket context, plans, SQL, write operations, database profile changes, execution, reports, or any other workflow output, and it must never bypass a human approval checkpoint defined by the workflow or MCP tool contract. Workflows not explicitly listed remain subject to the normal non-null `approved_by` and `approved_on` requirement.

Active workflow filenames use:

```text
skills/workflows/<client-name>_<project-type>_qaworkflow.md
skills/workflows/<client-name>_<project-type>_<workflow-variant>_qaworkflow.md
```

The filename is derived only from `client_name`, `project_type`, and the optional `workflow_variant`. Do not use any other metadata field to construct or select a workflow filename.

The reusable file `skills/workflows/clientname_project_qaworkflow.md` has `document_type: qa_workflow_template`. It is a non-active template and must never be used to execute a live ticket.

Do not select a workflow merely because its filename or contents appear similar. Stop, explain what is missing or ambiguous, and request clarification from an authorized user when:

- no exact workflow with the required approval metadata or an explicit approval-metadata exemption exists;
- multiple workflows match;
- routing metadata is missing;
- the ticket type is unsupported;
- workflow instructions conflict;
- required context is unavailable; or
- the correct action cannot be proven.

Do not invent fallback behavior.

## Following The Workflow Checklist

The selected workflow contains ordered checklist items under `## Steps`. Each checklist item defines its own:

- applicability and applicability rule;
- runtime checklist status;
- required inputs;
- permitted tools or systems;
- ordered agent actions;
- required Agent Skill when applicable;
- human approval requirements;
- expected checkpoint;
- completion evidence;
- skip reason; and
- failure path.

Permitted applicability values are `required`, `conditional`, `optional`, and `not_applicable`.

Permitted runtime checklist statuses are `not_started`, `in_progress`, `completed`, `skipped`, and `blocked`.

Do not mark a checklist item `completed` until its expected checkpoint and completion evidence are satisfied. Missing, `null`, unresolved, or contradictory action-critical values make the checklist item `blocked`; they must never be treated as permission to proceed. Follow the checklist item's failure path whenever it becomes blocked.

## Resolving Agent Skills

Agent Skills are declared directly inside the applicable checklist item using **Required Agent Skill**. They are not declared in workflow YAML metadata.

When **Required Agent Skill** is not `null`, resolve it through:

```text
skills/agent_skills/<skill-name>/SKILL.md
```

The checklist item's **Required Agent Skill** value, the Agent Skill folder name, and the `name` field inside `SKILL.md` must match exactly.

Before using a required Agent Skill:

1. Locate the exact `skills/agent_skills/<skill-name>/SKILL.md` path.
2. Read the complete `SKILL.md`.
3. Read supporting files only when `SKILL.md` references or requires them.
4. Follow the skill only for the checklist item that requested it.
5. Return control to the workflow checklist after completing the skill task.

An Agent Skill supports a checklist item but does not determine which client/project workflow applies. If a required skill is missing, conflicting, ambiguous, unavailable, or conflicts with this file, mark the checklist item `blocked` and stop instead of substituting another skill.

## Tool And System Boundaries

- Use Atlassian MCP only for authorized Jira and Atlassian context operations supported by the selected workflow.
- Use the database MCP in `MCP/` only for database profiles, connection checks, metadata inspection, and approved database operations.
- Keep Jira interpretation, client rules, QA decisions, and report ownership outside `MCP/`.
- Use named database profiles and approved secret-management mechanisms. Never place credentials in prompts, skills, ticket artifacts, logs, or reports.
- Treat database permissions as the final execution boundary.
- Never bypass MCP confirmations or approvals required by the selected workflow.

## Permanent Safety Rules

- Do not hallucinate ticket context, client rules, expected results, approvals, database structure, routing decisions, or escalation behavior.
- Do not continue when the applicable client workflow is unknown or unsupported.
- Do not execute SQL or switch database profiles without every approval required by the selected workflow and MCP tool contract.
- Do not automatically rewrite and rerun failed SQL unless the selected workflow permits it and required approval is obtained again.
- Prefer non-mutating validation. Explain and obtain explicit authorization for any proposed DML or DDL.
- Do not expose credentials, tokens, private keys, connection strings, or sensitive authentication details.
- Do not mix client source files, generated artifacts, operational logs, and final reports.
- Do not modify working project code merely to complete a ticket run.

## Code Documentation Convention

When explicitly authorized to modify project code, preserve the repository's collapsible documentation structure:

- wrap imports and module setup in `# region Imports and module setup` and its matching `# endregion`;
- wrap every class, function, and executable entry point in a clearly named region;
- give every module, class, and function a concise purpose-specific docstring;
- label nontrivial internal logical blocks with a collapsible region or an explanatory inline comment;
- use balanced `#region` and `#endregion` sections in PowerShell files; and
- run `tests/test_code_documentation.py` after code changes.

Comments must explain purpose, boundaries, or non-obvious decisions. Do not remove documentation regions merely to shorten a file.

## Context Recovery

If the agent loses all conversational context:

1. Read this file completely.
2. Inspect only the relevant repository structure and existing ticket workspace without changing files.
3. Re-establish the ticket ID and client identity from authoritative context.
4. Select and read the exact client workflow again.
5. Review existing ticket artifacts, logs, and approvals to determine the last confirmed state.
6. Stop, explain the uncertainty, and request clarification from an authorized user if the workflow or safe continuation point cannot be proven.
7. Never assume that an action was approved merely because an artifact exists.

## Changing Agent Behavior

Project-wide folder relationships, safety boundaries, and workflow-selection behavior belong in this file. Client/project-specific behavior belongs in eligible workflow files under `skills/workflows/`.

When requirements change:

- update this file only for rules that apply to every client;
- update the relevant client workflow for client-specific steps;
- request authorized clarification when no approved instruction defines organization-wide escalation behavior; and
- keep `docs/prd.md` synchronized as the human-facing project explanation.
