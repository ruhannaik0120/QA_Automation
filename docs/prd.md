# QA Automation Project

## Product Requirements and Design Document

| Document field | Value |
|---|---|
| Project | QA Automation |
| Document purpose | Complete project explanation, product requirements, architecture, operation, and future development guide |
| Primary audience | New developers, QA engineers, technical leads, AI-agent operators, and project stakeholders |
| Agent context entry point | `Basic_Instructions.md` |
| Client/project workflow location | `skills/workflows/` |
| Non-active workflow template | `skills/workflows/clientname_project_qaworkflow.md` |
| Reusable Agent Skill location | `skills/agent_skills/<skill-name>/SKILL.md` |
| Database subsystem documentation | `docs/MCP.md` |
| Current delivery model | Human-approved, AI-assisted QA workflow |

## 2. Executive Summary

The QA Automation project turns the requirements in a Jira ticket into a controlled QA validation run.

An AI agent coordinates the process. It first reads the permanent project instructions, selects one exactly matching and eligible client/project workflow from `skills/workflows/`, and then follows its ordered checklist. Eligibility requires normal administrative approval metadata or an exact exemption in an explicitly approved local run configuration. A checklist item may invoke one exact Agent Skill. If routing information, workflow coverage, eligibility, or a required skill is missing, ambiguous, or conflicting, the agent stops and requests authorized clarification instead of inventing a process.

The project is deliberately divided into separate responsibilities:

- **Atlassian MCP** provides Jira ticket information.
- **The AI agent** coordinates the workflow and prepares QA artifacts.
- **Client/project workflows** define stable procedures for supported client, project, and optional variant combinations.
- **Reusable Agent Skills** provide task-specific instructions for individual workflow stages.
- **The human operator** approves important decisions and execution steps.
- **The database MCP server in `MCP/`** provides controlled database access.
- **Database connectors** translate common MCP operations into database-specific operations.
- **Ticket storage** keeps working state and raw evidence for each ticket.
- **Root-level logs** record workflow and execution activity.
- **Root-level output** contains final HTML and Excel reports.

The system is not intended to give an AI unrestricted access to Jira or databases. Human approval, named database profiles, credential isolation, structured evidence, and database permissions are core design requirements.

## 3. The Problem Being Solved

Database-backed QA validation commonly involves several manual steps:

1. Read a Jira ticket and identify testable requirements.
2. Collect supporting attachments and linked documents, including files behind credential-protected links.
3. Translate the complete available context into a QA plan.
4. Determine which database systems contain the relevant evidence.
5. Inspect database schemas and column names.
6. Write validation SQL.
7. Review the SQL for correctness and safety.
8. Run the SQL against the correct environment.
9. Compare actual results with expected results.
10. Save evidence and explain failures.
11. Produce a report that another person can understand.

When these steps are performed informally, important context can be lost. Queries may be executed against the wrong system, approval decisions may not be recorded, raw execution success may be mistaken for a passed QA check, and results may not be reproducible.

This project standardizes that process while keeping a human in control.

## 4. Product Vision

The final working QA Automation system should allow an authorized user to provide a Jira ticket key and guide an AI agent through a repeatable, auditable workflow that produces reliable QA evidence and a clear final report.

The finished system should:

- understand the available Jira requirement context;
- accept local copies of Jira attachments and linked documents that the agent cannot access directly;
- keep external source files separate from workflow-generated artifacts;
- create consistent ticket-scoped working files;
- require human approval at high-impact checkpoints;
- support multiple database systems through one MCP interface;
- keep credentials outside prompts and generated artifacts;
- preserve raw evidence separately from final reports;
- clearly distinguish query execution from QA validation;
- allow failed SQL to be corrected, reapproved, and selectively rerun;
- produce structured JSON evidence;
- optionally produce HTML and Excel reports;
- support future database connectors without redesigning the workflow;
- support different client procedures without changing the permanent project instructions; and
- remain understandable to a new developer or operator.

## 5. Product Goals

### 5.1 Primary goals

1. Convert Jira requirements into specific and reviewable QA checks.
2. Make database validation available to MCP-compatible AI agents.
3. Require explicit human approval before SQL execution and environment changes.
4. Store external ticket inputs and generated QA evidence in separate, stable locations.
5. Make credential-protected supporting content available through authorized local downloads without giving credentials to the agent.
6. Keep operational logs and final reports in clearly separate locations.
7. Support PostgreSQL, Snowflake, MySQL, SQL Server, and an offline demo system through one MCP tool interface.
8. Produce results that can be audited, evaluated, and shared.
9. Make the system extensible for future connectors and broader QA workflows.
10. Prevent unsupported tickets from being processed through an assumed or hallucinated workflow.

### 5.2 Non-goals

The current project is not intended to:

- replace human QA judgment;
- automatically approve its own SQL;
- bypass database permissions;
- store database credentials in the repository;
- embed Jira-specific logic inside the database MCP server;
- treat successful SQL execution as automatic proof that a requirement passed;
- provide a production web dashboard;
- act as a general-purpose database administration tool; or
- run destructive database operations without explicit explanation and approval.

## 6. Beginner Concepts

### 6.1 What is QA automation?

Quality assurance, or QA, is the process of checking whether a system behaves as required. QA automation uses software to perform repeatable checks and collect evidence.

In this project, automation assists with requirement interpretation, SQL preparation, database execution, evidence handling, and report generation. A human still reviews the context and approves important actions.

### 6.2 What is an AI agent?

An AI agent is an AI assistant that can use configured tools and work with files. In this project, the agent acts as the workflow coordinator.

The agent can:

- retrieve ticket information through Atlassian MCP;
- create and update local QA artifacts;
- call database tools through the database MCP server;
- compare expected and actual results; and
- generate reports from saved evidence.

The agent does not receive unrestricted database credentials. It works through approved MCP tools and named database profiles.

### 6.3 What is MCP?

MCP stands for Model Context Protocol. It is a standard way for an AI client to discover and call tools exposed by an external service.

An MCP server publishes tools with structured inputs and outputs. In this project:

- Atlassian provides an MCP server for Jira access.
- This repository contains a separate MCP server for database access.

The database MCP server is only one component of the complete QA Automation project. See [MCP.md](MCP.md) for its implementation, connector, and tool documentation. Use [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation and environment setup.

### 6.4 What is a database profile?

A database profile is a named, locally configured set of connection settings. A profile identifies a database type, host, database, user, connection options, timeouts, and row limits.

The AI agent works with safe profile names such as:

```text
postgres-test
snowflake-qa
sqlserver-staging
```

Credentials remain in `MCP/.env` or an approved secret-management system. They must not be written into tickets, prompts, logs, reports, or committed files.

### 6.5 What is a ticket run?

A ticket run is one QA workflow associated with one Jira ticket or client QA request.

Every run uses a normalized ticket ID and stores its working state under:

```text
ticket_runs/<ticket-id>/
```

Examples:

```text
ticket_runs/KAN-6/
ticket_runs/ABC-123/
```

## 7. Current Implementation And Final Target

It is important to distinguish what exists now from what the complete product may become later.

### 7.1 Implemented now

The repository currently includes:

- permanent AI-agent orientation and repository-boundary instructions;
- a reusable, non-active client/project workflow template;
- separate locations for client/project workflows and reusable Agent Skills;
- explicit stop-and-clarification behavior for unknown, ambiguous, conflicting, or unsupported work;
- Atlassian MCP workspace configuration;
- a reusable database MCP server;
- named database profile handling;
- demo, PostgreSQL, Snowflake, MySQL, and SQL Server connectors;
- connection, metadata, diagnostics, profile, and query tools;
- SQL structural guardrails;
- ticket-run folder initialization;
- safe ticket ID normalization;
- separate `downloads/` and `generated/` ticket workspaces;
- a local-file fallback for supporting Jira content the agent cannot access directly;
- stable generated-artifact paths;
- root-level workflow logs;
- structured execution-result storage;
- HTML and Excel report generation;
- sensitive-field redaction during report generation;
- HTML escaping and Excel formula-injection protection;
- unit and workflow helper tests; and
- an offline demo connector for verification without a live database.

### 7.2 Current operating model

The current system is AI-assisted rather than a single unattended application.

The AI agent reads `Basic_Instructions.md` to recover its role, permanent boundaries, workflow-selection rules, and skill-resolution rules. It determines `client_name` from authoritative ticket or authorized-user context, obtains `project_type` from the Jira title or other authoritative ticket metadata, and determines `workflow_variant` only when explicitly required. It selects the exact eligible workflow under `skills/workflows/` and follows its ordered checklist. When a checklist item's **Required Agent Skill** is not `null`, the agent resolves it to `skills/agent_skills/<skill-name>/SKILL.md`. The outer workflow modules initialize folders and export saved data, but they do not retrieve Jira tickets, generate filenames, select workflows, validate workflow metadata, resolve skills, or execute database queries themselves.

### 7.3 Intended final development

The final working development should preserve the same boundaries while making the workflow consistently repeatable for every ticket. Regardless of the future AI client, user interface, scheduler, or deployment platform, the system should continue to enforce:

- one ticket-scoped working area per run;
- one explicitly selected and approved client workflow per run;
- a controlled stop and request for authorized clarification instead of guessed behavior for unsupported work;
- a clear boundary between external source files and generated workflow artifacts;
- an authorized local-download fallback for inaccessible supporting content;
- centralized logs;
- centralized final output;
- explicit approval checkpoints;
- named database profiles;
- one approved SQL statement per database MCP call;
- structured evidence;
- expected-versus-actual evaluation; and
- separation between orchestration and database execution.

Future interfaces may automate more coordination, but they must not remove these controls without an approved product and security decision.

## 8. System Architecture

### 8.1 High-level architecture

```text
                    +----------------------+
                    |    Human Operator    |
                    | reviews and approves |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |       AI Agent       |
                    | reads project rules  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Approved client and  |
                    | project workflow     |
                    +---+--------------+---+
                        |              |
            Jira context|              |database tools
                        v              v
              +---------+----+   +-----+-------------+
              | Atlassian MCP |   | Repository MCP   |
              | Jira access   |   | database access  |
              +--------------+   +-----+-------------+
                                        |
                       +----------------+----------------+
                       |                |                |
                       v                v                v
                  PostgreSQL        Snowflake       Other supported
                                                     databases

AI Agent also writes:

ticket_runs/<ticket-id>/                 logs/<ticket-id>.log   output/<ticket-id>/
downloads/ + generated/ workspace          shared activity log    final reports
```

### 8.2 Responsibility boundaries

| Component | Responsible for | Not responsible for |
|---|---|---|
| Human operator | Confirming client identity where needed, reviewing context, downloading protected source files through an authorized session, and making approvals required by the client workflow | Giving credentials to the agent or manually implementing every database connector operation |
| AI agent | Recovering project context, selecting one exact approved client/project workflow, resolving its required skills, coordinating approved work, and stopping when routing or skill coverage is uncertain | Inventing workflow rules or bypassing approvals, credentials, and database permissions |
| Client/project workflow | Defining stable procedures, approvals, systems, evidence, and outputs for one client, project, and optional workflow variant | Overriding project-wide security and folder boundaries or storing one ticket's generated state |
| Reusable Agent Skill | Teaching the agent how to perform one reusable task for the checklist item that names it through **Required Agent Skill** | Selecting which client/project workflow applies or overriding that workflow |
| Atlassian MCP | Retrieving Jira context available to the authenticated user | Database execution or report generation |
| Database MCP in `MCP/` | Profile operations, connection checks, metadata inspection, approved SQL execution | Jira interpretation, QA pass/fail decisions, or ticket report ownership |
| Database connector | Database-specific connections, metadata SQL, timeouts, row limits, and execution | Workflow orchestration |
| Workflow modules | Creating local ticket structure and exporting saved results | Calling Jira, MCP tools, or databases |
| Ticket `downloads/` | Preserving unmodified external files associated with the ticket | Holding AI-generated or workflow-generated artifacts |
| Ticket `generated/` | Preserving AI-generated workflow state and raw QA evidence | Holding external source documents, operational logs, or final reports |
| Root `logs/` | Recording non-secret workflow and execution activity | Holding raw credentials |
| Root `output/` | Holding final approved reports | Acting as the source of truth for raw execution evidence |

## 9. Repository Structure

```text
qa_automation/
|-- .vscode/
|   `-- mcp.json
|-- Basic_Instructions.md
|-- docs/
|   |-- Add_Agent_Skills.md
|   |-- MCP.md
|   `-- prd.md
|-- MCP/
|   |-- connectors/
|   |-- models/
|   |-- scripts/
|   |-- services/
|   |-- tests/
|   |-- tools/
|   |-- validation/
|   |-- .env.example
|   |-- config.py
|   |-- requirements.txt
|   `-- server.py
|-- logs/
|-- output/
|-- modules/
|   |-- __init__.py
|   |-- init_ticket_run.py
|   `-- export_results.py
|-- skills/
|   |-- workflows/
|   |   |-- clientname_project_qaworkflow.md
|   |   `-- approved client/project workflows
|   `-- agent_skills/
|       `-- <skill-name>/
|           |-- SKILL.md
|           `-- optional supporting files
|-- tests/
|   `-- test_e2e_helpers.py
|-- ticket_runs/
|-- requirements-e2e.txt
|-- ticket_run_config.example.json
`-- ticket_run_config.json
```

### 9.1 Top-level files and folders

| Path | Purpose |
|---|---|
| `Basic_Instructions.md` | Permanent project-wide rules, repository boundaries, safety requirements, workflow-selection rules, skill-resolution rules, and context-recovery instructions. |
| `docs/prd.md` | This project-wide PRD and handoff document. |
| `docs/MCP.md` | Detailed documentation for the reusable database MCP subsystem. |
| `docs/Add_Agent_Skills.md` | AI-agnostic manual process for reviewing, installing, verifying, and updating reusable Agent Skills. |
| `MCP/` | Database MCP implementation, connectors, services, tools, configuration, and tests. |
| `ticket_runs/` | Ticket-scoped workspaces containing external inputs under `downloads/` and workflow artifacts under `generated/`. Generated ticket folders are not committed. |
| `logs/` | Shared workflow and execution logs, one file per ticket run. |
| `output/` | Final generated reports organized by ticket ID. |
| `modules/` | Reusable outer-workflow Python modules for ticket initialization and result export. |
| `skills/workflows/` | Stable client/project procedures plus the non-active `clientname_project_qaworkflow.md` authoring template. |
| `skills/agent_skills/` | Reusable task-specific skill packages. Each package is named by its exact skill key and contains a required `SKILL.md` plus any optional supporting files. |
| `tests/` | Tests for the outer workflow helpers. |
| `ticket_run_config.json` | Machine-readable shared paths, schemas, resolution precedence, statuses, formats, and baseline controls. It contains no selected route. |
| `ticket_run_config.example.json` | Placeholder-only example for an optional, approved, Git-ignored `ticket_run_config.local.json` containing non-secret run-specific values. |
| `requirements-e2e.txt` | Outer workflow dependencies. It currently provides `openpyxl` for Excel export. |
| `.vscode/mcp.json` | Workspace configuration for Atlassian MCP and the local database MCP server. |

## 10. Ticket Artifact Model

### 10.1 Ticket naming convention

The standard path is:

```text
ticket_runs/<ticket-id>/
```

The helper normalizes ticket IDs to uppercase and permits safe letters, numbers, dots, underscores, and hyphens. Unsafe values are normalized with a deterministic hash when necessary to reduce naming collisions. Windows reserved filenames are also handled.

### 10.2 Stable ticket structure

```text
ticket_runs/<ticket-id>/
|-- downloads/
|   |-- requirements.pdf
|   |-- supporting-data.xlsx
|   `-- <other external ticket files>
`-- generated/
    |-- ticket_context.md
    |-- qa_plan.md
    |-- generated_sql/
    |   `-- generated_queries.sql
    |-- approvals/
    |   `-- approval_log.md
    `-- execution_results/
        `-- execution_result.json
```

The example files under `downloads/` are illustrative only. The initializer creates the empty folder but does not create fake external inputs.

No `logs/` or `output/` folder should be created inside a ticket directory. Operational logs remain under root `logs/`, and final reports remain under root `output/`.

### 10.3 Artifact definitions

| Artifact | Purpose | Created or updated by |
|---|---|---|
| `downloads/<source-file>` | Original external content associated with Jira, including attachments or local copies of protected linked documents | Authorized user or an agent that can legitimately access the source |
| `generated/ticket_context.md` | Organized Jira summary plus relevant context extracted from local downloaded files | AI agent using Atlassian MCP and `downloads/` |
| `generated/qa_plan.md` | QA objectives, checks, expected outcomes, required systems, and profile needs | AI agent after context approval |
| `generated/generated_sql/generated_queries.sql` | Proposed SQL mapped to stable QA check IDs | AI agent before SQL approval |
| `generated/approvals/approval_log.md` | Human approval and rejection history for required checkpoints | AI agent recording user decisions |
| `generated/execution_results/execution_result.json` | Structured raw database evidence and explicit QA evaluation | AI agent using database MCP responses |
| `logs/<ticket-id>.log` | Non-secret workflow, profile, execution, evaluation, and export activity | Initializer and AI agent |
| `output/<ticket-id>/report.html` | Final browser-readable report | Export helper after approval |
| `output/<ticket-id>/report.xlsx` | Final spreadsheet report | Export helper after approval |

### 10.4 Downloads are external inputs

`downloads/` exists because an AI agent may be unable to open a Jira attachment or linked document that requires a separate authenticated browser session, VPN, client portal, or other credential-protected access.

When that happens:

1. The agent identifies the inaccessible source and explains why it matters.
2. The authorized user opens the source using their own approved session.
3. The user downloads the file and places it in `ticket_runs/<ticket-id>/downloads/`.
4. The agent inventories and reads the supported local file.
5. Relevant information is incorporated into `generated/ticket_context.md`, with the source filename recorded for traceability.

The user must not give credentials, session cookies, access tokens, or private links containing secrets to the agent. Downloaded files should retain meaningful filenames where practical, must not be overwritten silently, and must be handled according to company data-classification and malware-scanning policy.

### 10.5 Generated contains workflow outputs

`generated/` contains only artifacts produced or maintained by the QA automation workflow. External PDFs, Word documents, spreadsheets, images, and similar source files do not belong there.

This separation makes it clear which material came from outside the system and which material represents the system's interpretation, plan, approvals, SQL, and evidence.

### 10.6 Why raw evidence and final output are separate

`generated/execution_results/execution_result.json` is the source evidence. It contains the structured data needed to audit or regenerate a report.

HTML and Excel files are presentation outputs. They may summarize or format the evidence for a stakeholder. Keeping them under `output/<ticket-id>/` prevents a final report from being confused with source workflow state.

## 11. Instruction And Workflow Architecture

The project separates permanent rules, client/project procedures, reusable task instructions, and ticket-specific state. Keeping these responsibilities separate prevents one ticket's details from becoming permanent behavior and prevents a reusable skill from selecting its own workflow.

| Layer | Location | Responsibility |
|---|---|---|
| Permanent project instructions | `Basic_Instructions.md` | Defines project-wide rules, repository boundaries, safety requirements, workflow-selection rules, skill-resolution rules, and context-recovery behavior. It does not contain one client's detailed ticket procedure. |
| Client/project workflows | `skills/workflows/` | Defines stable procedures for one client, project type, and optional workflow variant. It may reference exact Agent Skills for individual stages. |
| Reusable Agent Skills | `skills/agent_skills/<skill-name>/` | Defines reusable task-specific instructions in `SKILL.md`, with optional supporting material required by that skill. It does not select a client/project workflow. |
| Ticket-specific inputs and state | `ticket_runs/<ticket-id>/` | Keeps external source documents under `downloads/` and AI-generated or workflow-generated artifacts under `generated/`. |

### 11.1 Workflow Routing

The reusable workflow template uses this YAML frontmatter:

```yaml
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
```

For a completed workflow, `document_type` must be `qa_workflow`, `client_name` and `project_type` are mandatory, and `workflow_variant` is optional. Approval fields remain `null` until actual approval is provided. Shared configuration grants no approval-metadata exemptions by default. A workflow may retain null approval fields while active only when its exact path is explicitly listed in `workflow_approval.approval_metadata_exempt_workflows` in an approved, ignored `ticket_run_config.local.json`; all other workflows require non-null approval metadata before use.

The filename identifies the workflow; there is no separate workflow identifier. Completed workflows use one of these filenames:

```text
skills/workflows/<client-name>_<project-type>_qaworkflow.md
skills/workflows/<client-name>_<project-type>_<workflow-variant>_qaworkflow.md
```

The second form is used only when a variant is explicitly required. The filename is derived only from `client_name`, `project_type`, and the optional `workflow_variant`; other metadata must not affect it.

Examples:

```text
skills/workflows/nclh_edm_qaworkflow.md
skills/workflows/nclh_edm_reconciliation_qaworkflow.md
```

Workflow routing follows this exact process:

1. Determine `client_name` from authoritative ticket or authorized-user context.
2. Determine `project_type` from the Jira title or other authoritative ticket metadata.
3. Determine `workflow_variant` only when explicitly required.
4. Locate the workflow using the filename convention.
5. Read and validate its YAML frontmatter.
6. Confirm that `document_type` is exactly `qa_workflow`, `client_name` matches, `project_type` matches, and `workflow_variant` matches when required.
7. Confirm that `approved_by` and `approved_on` are both not `null` unless the exact selected path is listed in `workflow_approval.approval_metadata_exempt_workflows` in an explicitly approved local run configuration.
8. Use only that exact workflow.

The reusable template at `skills/workflows/clientname_project_qaworkflow.md` has `document_type: qa_workflow_template`. It is non-active and must never be selected for a live ticket.

Missing, ambiguous, duplicate, unmatched, or ineligible workflows cause the agent to stop before client-specific work and request clarification from an authorized owner. An eligible workflow has the required non-null approval metadata or an exact exemption in an explicitly approved local run configuration. It must not be chosen merely because its filename or contents appear similar.

The exemption applies only to administrative workflow metadata. It does not satisfy or bypass context approval, execution approval, write-operation approval, profile-switch approval, report approval, or any other runtime checkpoint.

This routing process currently documents required AI-agent behavior. Automatic filename generation, metadata validation, and workflow routing have not been implemented in Python.

The routing flow is:

```text
Read Basic_Instructions.md
      |
      v
Determine client_name from authoritative context
      |
      v
Determine project_type and explicit workflow_variant when required
      |
      v
Locate exact filename and validate frontmatter and approval fields
      | Yes                         | No or uncertain
      v                             v
Read complete workflow        Stop and request authorized clarification
      |
      v
Follow ordered checklist items under Steps
      |
      v
Resolve an item's Required Agent Skill when it is not null
      |
      v
Store external inputs in downloads/ and generated state in generated/
```

### 11.2 Workflow Checklist And Agent Skill Resolution

The `## Steps` section of a completed workflow is an ordered checklist. Each checklist item defines:

- its checklist item ID and objective;
- applicability and its applicability rule;
- entry conditions and required inputs;
- **Required Agent Skill** when applicable;
- permitted tools or systems and ordered actions;
- approval requirements;
- expected checkpoint and completion evidence;
- generated or updated artifact;
- skip reason; and
- failure path.

Permitted applicability values are `required`, `conditional`, `optional`, and `not_applicable`. Runtime checklist status must be `not_started`, `in_progress`, `completed`, `skipped`, or `blocked`.

An item cannot be `completed` until its expected checkpoint and completion evidence are satisfied. A `conditional` or `optional` item may be `skipped` only when its applicability rule permits it, and every skipped item must record a reason. Missing, `null`, contradictory, or unresolved action-critical values make the item `blocked`; they must never be treated as permission to proceed.

Each reusable Agent Skill has its own folder under `skills/agent_skills/`. Every skill package must contain `SKILL.md`. Depending on that skill's needs, the package may also contain supporting references, scripts, templates, assets, or examples.

An Agent Skill is declared directly inside the applicable checklist item using **Required Agent Skill**. Workflow YAML does not contain skill lists. When **Required Agent Skill** is not `null`, it resolves to:

```text
skills/agent_skills/<skill-name>/SKILL.md
```

The checklist item's **Required Agent Skill** value, the `<skill-name>` folder name, and the `name` in `SKILL.md` must match exactly. The agent reads `SKILL.md`, uses supporting files only as directed, applies the skill only to that checklist item, and then returns control to the workflow checklist.

Agent Skills do not determine the client, project type, workflow variant, or applicable workflow. A missing, unavailable, ambiguous, or conflicting required skill makes the checklist item `blocked`; the agent must stop rather than substitute a similar skill. The project uses explicit paths and metadata and does not depend on native skill discovery from any particular AI product.

### 11.3 Optional QA Capability Sequence

The remaining subsections document QA planning, database validation, approval, evidence, and reporting capabilities currently available in the repository. They are not one universal workflow and are not the default process for every client. The exact selected workflow decides which stages apply, their order, their required Agent Skills, and their approval checkpoints. A workflow does not need to use SQL, a database, a QA plan, or report export unless its approved procedure requires them, and no workflow may override the permanent security, credential, MCP, or folder boundaries in `Basic_Instructions.md`.

### 11.4 Step 1: Initialize the run

From the repository root:

```powershell
.\.venv\Scripts\python.exe .\modules\init_ticket_run.py ABC-123
```

The initializer:

- normalizes the ticket ID;
- creates the ticket directory with primary `downloads/` and `generated/` subdirectories;
- creates missing template artifacts without overwriting existing files;
- leaves `downloads/` empty until real external ticket files are added;
- creates `logs/<ticket-id>.log` if it does not exist;
- does not create a ticket-local logs folder;
- does not create a ticket-local output folder;
- does not contact Jira;
- does not contact an MCP server; and
- does not connect to a database.

The initializer is idempotent. Running it again does not overwrite completed work.

### 11.5 Step 2: Retrieve Jira and supporting context

The user supplies a Jira ticket key. The AI agent uses Atlassian MCP to retrieve the ticket information visible to the authenticated Atlassian account.

Relevant context can include:

- summary;
- description;
- acceptance criteria;
- comments;
- linked issues;
- attachments and linked supporting documents;
- labels and priority;
- available project context; and
- information needed to define QA checks.

If the agent cannot access a credential-protected link or attachment, it asks the authorized user to download the file through their own session and place it under `ticket_runs/<ticket-id>/downloads/`. The agent must not ask for the user's credentials, tokens, or session data.

The agent inventories supported files in `downloads/`, extracts relevant context, and notes any file it cannot safely read. The combined organized context is saved to `generated/ticket_context.md`, with downloaded filenames referenced where they support a requirement.

### 11.6 Step 3: Approve ticket context

The AI agent must stop and ask the user whether the saved context is complete enough for planning.

The user may approve it, add missing information, ask the agent to retrieve the Jira ticket again, or place additional protected source files in `downloads/`. QA planning cannot begin until the context is explicitly approved.

The decision is recorded in `generated/approvals/approval_log.md`.

### 11.7 Step 4: Create the QA plan

The AI agent converts the approved requirements into concrete checks.

Each check should identify:

- a stable check ID;
- the requirement being validated;
- the expected result;
- the evidence required;
- whether database validation is required;
- the required database system and named profile; and
- any important assumptions or limitations.

The plan is saved to `generated/qa_plan.md`.

### 11.8 Step 5: Inspect metadata and prepare SQL

When schema details are uncertain, the agent should use database MCP metadata tools before writing SQL. It should inspect available databases, tables, and columns rather than guessing names.

Proposed SQL is saved to `generated/generated_sql/generated_queries.sql`. Every statement must map to a stable check ID.

Validation queries should normally be non-mutating. If DML or DDL is genuinely required, the agent must explain the effect and obtain explicit approval for that statement.

### 11.9 Step 6: Approve SQL

The agent shows or references the proposed SQL and explains what every statement checks.

No SQL may be executed until the user approves it. If an approved statement changes, the changed statement must be approved again.

### 11.10 Step 7: Approve and switch database profiles

Every target database or environment is represented by a named profile.

Before switching profiles, the agent explains:

- which profile is required;
- which database system it represents;
- why the switch is necessary; and
- which checks will use it.

The user must approve every system, environment, or profile switch.

### 11.11 Step 8: Execute approved SQL

The agent sends one exact approved SQL statement per database MCP call.

It must not send:

- the complete organizational SQL file as one request;
- multiple statements in one call;
- comments used only to organize the SQL file; or
- changed SQL that has not been reapproved.

Each response is associated with its stable check ID and stored in `generated/execution_results/execution_result.json`.

### 11.12 Step 9: Evaluate expected versus actual

Database execution and QA evaluation are different states.

An MCP response with `success=true` means the database accepted and executed the SQL. It does not mean the business requirement passed.

The agent compares the actual result with the expected result and assigns an explicit validation status:

| Status | Meaning |
|---|---|
| `passed` | The actual evidence satisfies the expected outcome. |
| `failed` | The actual evidence does not satisfy the expected outcome. |
| `executed_not_evaluated` | SQL ran successfully, but expected-versus-actual evaluation is incomplete. |
| `execution_failed` | The SQL did not execute successfully. |

### 11.13 Step 10: Correct and selectively rerun failures

If a query fails because of incorrect SQL, schema names, or column names:

1. inspect the actual metadata;
2. correct only the affected query;
3. explain the correction;
4. ask for approval again;
5. rerun only the failed or changed check; and
6. update the structured evidence and logs.

A successful retry must not erase the history of the earlier failure from the operational log.

### 11.14 Step 11: Approve report output

The user chooses one format:

| Format | Result |
|---|---|
| `json_only` | Keep `generated/execution_results/execution_result.json`; create no HTML or Excel report. |
| `html` | Create `output/<ticket-id>/report.html`. |
| `excel` | Create `output/<ticket-id>/report.xlsx`. |
| `both` | Create both final report files. |

HTML or Excel generation must not occur before the user chooses the format.

### 11.15 Step 12: Export the report

Examples:

```powershell
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format json_only
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format html
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format excel
.\.venv\Scripts\python.exe .\modules\export_results.py ABC-123 --format both
```

The exporter reads the saved JSON evidence. It does not call Jira, an MCP server, or a database.

## 12. Reference Human Approval Requirements

Each active client/project workflow must declare its exact approval checkpoints. The checkpoints below are supported examples for workflows that use the documented QA and database capabilities; they are not automatically required by every workflow. A workflow may add or refine checkpoints, but it cannot bypass MCP confirmations, database permissions, or permanent safety controls.

| Checkpoint | Required before | Evidence location |
|---|---|---|
| Ticket context approval | QA planning | `generated/approvals/approval_log.md` |
| SQL approval | Executing each new or changed SQL statement | `generated/approvals/approval_log.md` |
| Profile or environment approval | Every database profile/system switch | `generated/approvals/approval_log.md` |
| Export approval | Creating final HTML or Excel reports | `generated/approvals/approval_log.md` |

When these checkpoints apply, the agent must pause. A previous approval does not automatically approve later changes.

## 13. Database MCP Subsystem

### 13.1 Role in the project

The `MCP/` folder contains the reusable database execution subsystem. It gives MCP-compatible AI clients one stable tool interface across multiple database systems.

It is intentionally independent from Jira and ticket orchestration.

### 13.2 Supported connectors

The current connector registry supports:

- `demo`;
- `postgresql`;
- `snowflake`;
- `mysql`; and
- `sqlserver`.

The demo connector supports offline setup and testing without database credentials.

### 13.3 Main MCP capabilities

The MCP server exposes tools for:

- listing safe database profile information;
- reloading configuration;
- switching profiles with confirmation;
- returning redacted diagnostics;
- testing connections;
- checking connector health;
- listing databases;
- listing tables;
- describing table columns;
- suggesting likely column names;
- executing one approved SQL statement; and
- returning structured results and errors.

The exact tool names, response contracts, profile model, AI-client integration contract, and connector extension process are documented in [MCP.md](MCP.md).

### 13.4 MCP boundary rules

- Jira logic must stay outside `MCP/`.
- Ticket artifacts must stay outside `MCP/`.
- Reports and workflow logs must stay outside `MCP/`.
- Database drivers must remain inside their connector boundary.
- Credentials must not be included in MCP tool output.
- Database permissions remain the final execution boundary.

## 14. Execution Result Contract

The recommended structure for `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json` is:

```json
{
  "schema_version": "1.0",
  "ticket_id": "ABC-123",
  "summary": {
    "status": "validation_passed"
  },
  "query_results": [
    {
      "check_id": "CHECK-1",
      "execution_success": true,
      "validation_status": "passed",
      "expected": "No duplicate active records",
      "actual": "0 duplicate records",
      "metadata": {
        "profile": "postgres-test"
      },
      "row_count": 1,
      "rows": [
        {
          "duplicate_count": 0
        }
      ]
    }
  ],
  "errors": []
}
```

The exporter also accepts supported raw MCP response shapes, but raw execution success is reported as `executed_not_evaluated` until an explicit QA evaluation is added.

The result must not contain credentials, tokens, private keys, or secret-bearing connection strings.

## 15. Report Generation

### 15.1 HTML reports

HTML reports are generated with Python standard-library functionality. Dynamic content is HTML-escaped before it is written.

### 15.2 Excel reports

Excel reports use `openpyxl`, declared separately in `requirements-e2e.txt` because spreadsheet reporting belongs to the outer QA workflow rather than the database MCP server.

Excel output protects against formula injection and removes invalid control characters from cell content.

### 15.3 Report validation and safety

Before creating a report, the exporter:

- confirms the execution-result file exists;
- confirms the file contains valid JSON;
- verifies a declared ticket ID matches the requested run;
- rejects unfinished empty evidence for HTML or Excel output;
- redacts credential-like keys and values;
- builds QA summary counts from actual result statuses; and
- writes generated output under `output/<ticket-id>/`.

## 16. Logging And Auditability

All workflow and execution activity is recorded under the single root-level logs folder:

```text
logs/<ticket-id>.log
```

Logs should record:

- timestamps;
- ticket initialization;
- Jira retrieval activity;
- context updates;
- approval outcomes;
- profile switches using non-secret profile names;
- executed check IDs;
- execution outcomes;
- evaluation activity;
- corrections and retries; and
- report export activity.

Logs must not record:

- passwords;
- access tokens;
- private keys;
- secret connection strings;
- full credential configuration; or
- sensitive values that are not required for auditing the QA workflow.

## 17. Security Requirements

### 17.1 Credential handling

- Store local database credentials only in ignored `MCP/.env` configuration or an approved secret manager.
- Never commit `MCP/.env`.
- Never request that a user paste credentials into chat.
- Never store credentials in ticket artifacts, logs, JSON results, or reports.
- Keep OAuth and Atlassian authentication outside committed files.

### 17.2 Downloaded source files

- Do not ask users to share credentials, tokens, cookies, or authenticated URLs with the AI agent.
- Ask an authorized user to download inaccessible Jira-linked content through their own approved session.
- Store the resulting source file only under the ticket's `downloads/` folder.
- Treat downloaded files as untrusted until they satisfy company malware-scanning and data-handling policy.
- Preserve source files without silently overwriting or modifying them.
- Do not commit ticket downloads to Git.

### 17.3 Least privilege

Every database profile should use the least privilege required for its QA checks. Validation should normally use approved test or staging environments.

Database account permissions are the final authority. The MCP server cannot bypass permissions denied by the database.

### 17.4 SQL safety

- Prefer read-only validation SQL.
- Require approval before execution.
- Execute one statement per MCP call.
- Explain any DML or DDL separately.
- Do not automatically rewrite and rerun failed SQL without approval.
- Apply configured timeout and row limits.

### 17.5 Output safety

Reports can contain sensitive business data even when credentials are removed. Users must review outputs before sharing them outside the approved audience.

## 18. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall accept a Jira ticket key or equivalent run identifier. |
| FR-02 | The system shall create a stable, safely normalized ticket-run path with `downloads/` and `generated/` as its primary subfolders. |
| FR-03 | The system shall support authorized Jira context retrieval through Atlassian MCP when required by the selected client workflow. |
| FR-04 | The workflow shall support authorized local copies of inaccessible Jira attachments and links under `downloads/` without collecting user credentials. |
| FR-05 | The workflow shall keep external source files in `downloads/` and system-produced artifacts in `generated/`. |
| FR-06 | The system shall support organized ticket context in `generated/ticket_context.md` when required by the selected client workflow. |
| FR-07 | Each client workflow shall define its required context review and approval behavior. |
| FR-08 | Each client workflow shall define its required QA plan, checks, and expected outcomes. |
| FR-09 | Proposed SQL shall map to stable check IDs whenever database validation applies. |
| FR-10 | The workflow shall require approval before every new or changed SQL execution. |
| FR-11 | Database profile or environment switches shall satisfy both the selected client workflow and MCP confirmation requirements. |
| FR-12 | Database operations shall be performed through the database MCP server. |
| FR-13 | Each MCP query call shall contain one approved SQL statement. |
| FR-14 | Database execution evidence shall be stored as structured JSON under `generated/` whenever database validation applies. |
| FR-15 | Execution success and QA validation status shall remain separate. |
| FR-16 | Client workflows using database validation shall define correction, reapproval, and selective-rerun behavior. |
| FR-17 | All operational logs shall be stored under root `logs/`. |
| FR-18 | Ticket folders shall not contain logs or final report output. |
| FR-19 | Final reports shall be stored under `output/<ticket-id>/`. |
| FR-20 | Each client workflow shall define allowed report formats and required export approval. |
| FR-21 | Report generation shall redact credential-like values. |
| FR-22 | The database layer shall support extension through additional connectors. |
| FR-23 | The agent shall read `Basic_Instructions.md` when starting, resuming, or recovering context. |
| FR-24 | Every completed workflow shall be stored under `skills/workflows/` using `<client-name>_<project-type>_qaworkflow.md` or, when explicitly required, `<client-name>_<project-type>_<workflow-variant>_qaworkflow.md`. |
| FR-25 | The agent shall route by authoritative `client_name`, `project_type`, and optional `workflow_variant`, locate the exact filename, and validate its frontmatter. |
| FR-26 | The agent shall use only a workflow whose `document_type` is `qa_workflow`, routing metadata matches exactly, and approval metadata is non-null unless the exact workflow path has an exemption in an explicitly approved local run configuration; invalid or uncertain routing shall stop for authorized clarification. |
| FR-27 | `skills/workflows/clientname_project_qaworkflow.md` shall retain `document_type: qa_workflow_template`, remain non-active, and never be selected for a live ticket. |
| FR-28 | Every reusable Agent Skill shall be stored under `skills/agent_skills/<skill-name>/` with a required `SKILL.md` and optional skill-specific supporting files. |
| FR-29 | A checklist item's **Required Agent Skill**, its skill folder name, and the `SKILL.md` metadata name shall match exactly; missing or conflicting required skills shall block the item. |
| FR-30 | Every workflow step shall be an ordered checklist item whose applicability, runtime status, checkpoint, evidence, skip behavior, and failure path follow the documented checklist contract. |

## 19. Non-Functional Requirements

### 19.1 Safety

The system must fail clearly when client workflow selection, ticket coverage, configuration, paths, SQL structure, evidence, or dependencies are invalid. It must not silently continue past required approval gates or improvise an unsupported process.

### 19.2 Auditability

Every check should be traceable from requirement to QA plan, proposed SQL, approval, MCP response, validation status, and final report.

### 19.3 Maintainability

Permanent project instructions, client/project workflows, reusable Agent Skills, ticket-generated state, workflow modules, MCP tools, services, validation, and database connectors must remain separated. Workflow or skill changes should not require MCP changes, and a new connector should not require rewriting the permanent project instructions.

Every source file must preserve the collapsible code-documentation convention: labeled module setup, class, function, entry-point, and nontrivial internal sections; purpose-specific module/class/function docstrings; and balanced regions. `tests/test_code_documentation.py` enforces the structural parts of this convention.

### 19.4 Portability

The database server uses MCP over standard input/output and can be used by different compatible AI clients. Files use relative repository structure rather than developer-specific committed paths.

### 19.5 Reliability

Ticket initialization must be idempotent. Report generation must validate its input, and temporary report files must not replace final files until writing succeeds.

### 19.6 Testability

Normal automated tests should not require live Jira access or a live external database. Live connectivity tests should remain explicit and opt-in.

## 20. Setup Reference

Installation, environment configuration, MCP-client registration, Atlassian authentication, and first-run verification are centralized in [SETUP_GUIDE.md](SETUP_GUIDE.md). This PRD intentionally does not duplicate those procedures.
## 21. Normal Operating Procedure

1. Read `Basic_Instructions.md` completely.
2. Establish the ticket ID and determine `client_name` from authoritative ticket or authorized-user context.
3. Determine `project_type` from the Jira title or other authoritative ticket metadata and determine `workflow_variant` only when explicitly required.
4. Locate the exact filename under `skills/workflows/`, validate matching frontmatter, and confirm `approved_by` and `approved_on` are not `null` unless the exact path is listed in `workflow_approval.approval_metadata_exempt_workflows` in an explicitly approved local run configuration.
5. If routing is missing, ambiguous, conflicting, or unsupported, stop and request clarification from an authorized owner.
6. Read the selected workflow completely and state which workflow is active.
7. Follow its ordered checklist and resolve an item's **Required Agent Skill** to `skills/agent_skills/<skill-name>/SKILL.md` only when that value is not `null`.
8. Confirm the tools and systems required by the workflow and its skills are available.
9. Initialize and use the ticket workspace according to the shared folder contract.
10. Follow only the selected workflow's exact stages and approval checkpoints.
11. Keep external inputs, generated artifacts, logs, and final reports in their assigned locations.
12. On context loss, repeat workflow selection and verify the last approved state before continuing.

## 22. Error Handling And Recovery

### 22.1 The client workflow is unknown or unsupported

- Stop before client-specific planning, SQL generation or execution, profile switching, and final report generation.
- Identify the unresolved client, project type, workflow variant, metadata conflict, skill conflict, or missing authoritative context.
- Contact the project manager or designated QA workflow owner.
- Do not use the closest-looking workflow or the workflow template as a substitute.

### 22.2 Atlassian tools are unavailable

- Confirm the Atlassian server is running in the AI client.
- Confirm browser login completed successfully.
- Restart or reload the AI client if the server was added after the session started.
- Do not invent missing Jira context.

### 22.3 A Jira attachment or supporting link is inaccessible

- Do not ask for or store the user's credentials, session cookie, token, or authenticated URL.
- Ask an authorized user to download the source through their approved browser session.
- Place the original file under `ticket_runs/<ticket-id>/downloads/` using a meaningful filename.
- Apply company malware-scanning and data-handling requirements before opening it.
- Review the local file and cite its filename in `generated/ticket_context.md`.
- Record any file that cannot be safely or reliably read; do not invent its contents.

### 22.4 Database MCP tools are unavailable

- Confirm `.vscode/mcp.json` points to the correct `.venv` and `MCP/server.py`.
- Confirm the working directory is `MCP`.
- Run the verification script.
- Restart the MCP server and AI client.

### 22.5 A profile is not ready

- List profiles and inspect safe readiness issues.
- Correct `MCP/.env` without exposing credentials.
- Reload MCP configuration with confirmation or restart the MCP process.
- Test the connection before running QA SQL.

### 22.6 A query references an incorrect column

- Describe the real table through MCP metadata tools.
- Use column suggestions when appropriate.
- Correct only the failed SQL.
- Ask for approval again.
- Rerun only affected checks.

### 22.7 A report cannot be generated

- Confirm `ticket_runs/<ticket-id>/generated/execution_results/execution_result.json` exists and contains valid JSON.
- Confirm the ticket ID matches the requested export.
- Confirm execution evidence or errors are present.
- Install `requirements-e2e.txt` for Excel output.
- Confirm the target output file is not locked by another application.

## 23. Testing And Quality Gates

### 23.1 Outer workflow tests

`tests/test_e2e_helpers.py` verifies:

- ticket ID normalization and collision resistance;
- idempotent ticket initialization;
- creation of the two primary ticket folders, `downloads/` and `generated/`;
- stable generated-artifact locations;
- preservation of an empty input-only `downloads/` folder until real sources are added;
- absence of ticket-local logs and output;
- QA status calculation;
- evidence validation;
- recursive sensitive-value redaction;
- HTML escaping;
- Excel formula protection;
- HTML and Excel output generation; and
- the end-to-end helper flow using temporary test directories.

`tests/test_code_documentation.py` verifies module docstrings, class and function docstrings, collapsible region coverage, and balanced Python and PowerShell regions across the repository.

### 23.2 MCP tests

`MCP/tests/` verifies configuration, connectors, connector registration, service behavior, profile switching, SQL guardrails, response models, architecture boundaries, tool wrappers, limits, diagnostics, and demo behavior.

### 23.3 Live system testing

Normal automated tests should use mocks or the demo connector. Live Jira and database tests require explicit credentials, network access, approved environments, and operator intent.

## 24. Extensibility

### 24.1 Adding a database connector

New database systems are added inside `MCP/connectors/` by implementing the shared connector interface, registering the connector, adding its driver, adding tests, and documenting profile requirements.

The complete connector procedure is in [MCP.md](MCP.md).

### 24.2 Adding a report format

A new report format should:

- read the same structured execution evidence;
- preserve sensitive-value redaction;
- validate ticket ownership and evidence completeness;
- write only under `output/<ticket-id>/`;
- require explicit user approval; and
- include focused tests.

### 24.3 Adding another requirement source

A future source such as another ticketing system may be added to the outer workflow. It must not be embedded inside the database MCP server. The source adapter should produce the same organized ticket-context artifact expected by the planning stage.

### 24.4 Adding another AI client

Any client that supports the required MCP transports can use the project if it can:

- connect to Atlassian MCP;
- launch the local database MCP server;
- read and write repository files;
- stop for user approvals; and
- preserve the documented artifact contract.

### 24.5 Adding a client workflow

To onboard a client:

1. Copy `skills/workflows/clientname_project_qaworkflow.md` to the appropriate `<client-name>_<project-type>_qaworkflow.md` or `<client-name>_<project-type>_<workflow-variant>_qaworkflow.md` path under `skills/workflows/`.
2. Define exact `client_name`, `project_type`, and optional `workflow_variant` routing metadata from authoritative client/project rules.
3. Replace template prompts with stable client/project requirements and complete ordered checklist items for context, systems, approvals, evidence, reports, and escalation contacts.
4. Declare a reusable capability through **Required Agent Skill** only inside the checklist item that needs it, using a package under `skills/agent_skills/<skill-name>/`.
5. Confirm that the workflow respects `Basic_Instructions.md` and does not embed client logic inside `MCP/` or `modules/`.
6. Set `document_type` to `qa_workflow` and have the designated QA workflow owner populate `approved_by` and `approved_on` before the workflow is used, unless an authorized project owner adds the exact path to `workflow_approval.approval_metadata_exempt_workflows` in an explicitly approved local run configuration.
7. Test the workflow against representative non-production tickets, including exact-match, no-match, ambiguous-routing, unsupported, and required-skill failure cases.

Never make the template itself active, and never create a client workflow by guessing from one ticket.

### 24.6 Adding an Agent Skill

Create one folder at `skills/agent_skills/<skill-name>/` and add its required `SKILL.md`. A checklist item's **Required Agent Skill** value, the folder name, and the `SKILL.md` metadata name must match exactly. Add references, scripts, templates, assets, or examples only when that skill needs them, and document from `SKILL.md` how they are used.

An Agent Skill should teach one reusable task and remain limited to the checklist item that invokes it. It must not contain client/project routing logic, select a workflow, override `Basic_Instructions.md`, or store ticket-specific information. Control returns to the workflow checklist after the skill finishes. The project resolves skills by explicit path and metadata, so a skill must work without relying on product-specific native discovery.

## 25. Known Boundaries And Limitations

- The AI agent currently coordinates the workflow; there is no standalone workflow dashboard.
- Run-specific configuration resolution is currently instruction-driven. Future hardening should add an executable resolver that loads, merges, validates, and reports conflicts between authoritative Jira context, selected workflow metadata, and `ticket_run_config.local.json`.
- Client workflow selection currently depends on authoritative user or ticket context; there is no central client-routing service.
- The repository contains a non-active workflow template; a workflow becomes usable only after a separately named copy has complete routing metadata and either explicit administrative approval metadata or an exact exemption in an explicitly approved local run configuration.
- Missing, ambiguous, conflicting, or unsupported routing and required-skill problems require clarification from the project manager or designated QA workflow owner.
- Jira retrieval depends on Atlassian authentication and account permissions.
- The agent may be unable to open credential-protected external links referenced by Jira. An authorized user must download that content to the ticket's `downloads/` folder when it is needed for the run.
- Live database execution depends on network access, drivers, profile configuration, and database permissions.
- The workflow modules do not call Jira or databases directly.
- Human approvals are workflow rules coordinated by the agent and recorded in files.
- JSON evidence must be evaluated explicitly before a successful query can be called a passed QA check.
- Generated reports may contain sensitive business data and require review before distribution.
- Root logs are local text evidence rather than a centralized enterprise observability platform.

These boundaries do not prevent future expansion, but future development should preserve the security and responsibility model unless it is deliberately redesigned and approved.

## 26. Final Acceptance Criteria

The complete project is considered ready for a controlled ticket run when:

1. A new developer can set up the environment from documented steps.
2. Atlassian MCP authentication can retrieve an authorized Jira ticket.
3. The database MCP server starts and exposes its expected tools.
4. The demo connector passes without live credentials.
5. Required live database profiles report ready before use.
6. `Basic_Instructions.md` can restore the agent's project role and folder relationships without prescribing one client's exact procedure.
7. An exact eligible client/project workflow can be selected by authoritative `client_name`, `project_type`, optional `workflow_variant`, matching frontmatter, and either non-null approval fields or an exact exemption in an explicitly approved local run configuration.
8. Unknown, ambiguous, conflicting, and unsupported routing or required-skill problems stop for authorized clarification without client-specific execution.
9. A ticket ID creates `ticket_runs/<ticket-id>/downloads/` and `ticket_runs/<ticket-id>/generated/` with the documented generated-artifact structure.
10. Inaccessible supporting sources can be supplied through an authorized local download without exposing credentials to the agent.
11. External source files remain under `downloads/`, and all workflow-produced ticket artifacts remain under `generated/`.
12. No logs or final report folders are created inside the ticket directory.
13. The agent stops at every approval checkpoint required by the selected client workflow.
14. SQL execution and profile changes follow the selected workflow and MCP confirmation contract.
15. Raw evidence records execution success separately from validation status where database validation applies.
16. Shared activity is written to `logs/<ticket-id>.log`.
17. Approved reports are written to `output/<ticket-id>/` when required by the client workflow.
18. Credentials are absent from committed files, artifacts, skills, logs, reports, and downloads.
19. Outer workflow and MCP tests pass.
20. MCP implementation remains reusable and independent from client-specific workflow logic.

## 27. Handoff Checklist

Before handing the project to another developer or team:

1. Confirm the repository contains no real `.env` or secret files.
2. Confirm `MCP/.env.example` uses only safe demo values.
3. Run `MCP/scripts/verify.ps1`.
4. Confirm `.vscode/mcp.json` uses repository-relative paths.
5. Confirm `Basic_Instructions.md` describes permanent agent behavior and does not contain one client's detailed procedure.
6. Confirm every active workflow under `skills/workflows/` follows the filename convention, has exact matching routing metadata, uses `document_type: qa_workflow`, and has either non-null approval fields or an exact entry in the approved local run configuration's `workflow_approval.approval_metadata_exempt_workflows`.
7. Confirm `skills/workflows/clientname_project_qaworkflow.md` retains `document_type: qa_workflow_template` and every checklist-item **Required Agent Skill** resolves exactly under `skills/agent_skills/`.
8. Confirm `ticket_run_config.json` matches the documented shared artifact paths and baseline controls.
9. Confirm generated ticket runs, logs, and outputs are not committed.
10. Give the recipient this document for the project overview.
11. Give the recipient `MCP.md` for database subsystem behavior and extension details, and `SETUP_GUIDE.md` for installation and environment setup.
12. Demonstrate exact workflow selection, one stop-and-clarification case, required-skill resolution, and one offline MCP demo before connecting to live systems.

## 28. Glossary

| Term | Meaning |
|---|---|
| AI agent | The AI client coordinating the QA workflow and using MCP tools. |
| Approval checkpoint | A required pause where a human authorizes the next action. |
| Artifact | A file produced or updated during a ticket run. |
| Agent Skill | Reusable task-specific instructions stored at `skills/agent_skills/<skill-name>/SKILL.md`; it supports the checklist item that names it but does not select or replace a client/project workflow. |
| Client/project workflow | An eligible file under `skills/workflows/` with `document_type: qa_workflow`, exact routing metadata, ordered checklist items for one client, project type, and optional workflow variant, and either approval metadata or an exact exemption in an explicitly approved local run configuration. |
| Connector | Database-specific implementation behind the common MCP interface. |
| Downloads | External source files associated with a ticket, including authorized local copies of inaccessible attachments or linked documents. |
| Execution success | Confirmation that a SQL statement ran, not that the QA expectation passed. |
| Workflow routing | Exact matching of authoritative client, Jira-title project type, and optional workflow variant against eligible workflow metadata. |
| Generated artifacts | Ticket-scoped files produced by the AI agent, initializer, or QA workflow. |
| Jira context | Ticket information used to understand and plan QA validation. |
| MCP | Model Context Protocol, used by AI clients to discover and call tools. |
| Named profile | A safe name referring to locally configured database connection settings. |
| QA plan | Document describing checks, expected outcomes, systems, and evidence requirements. |
| Ticket run | One complete QA workflow for one ticket or client request. |
| Validation status | Explicit expected-versus-actual QA result such as passed or failed. |

## 29. Documentation Map

Use the project documentation in this order:

1. **`docs/prd.md`** - understand the complete product, architecture, requirements, operation, and design.
2. **`Basic_Instructions.md`** - restore the agent's role, repository relationships, permanent boundaries, and workflow-selection behavior.
3. **`skills/workflows/<client-name>_<project-type>[_<workflow-variant>]_qaworkflow.md`** - follow the one exact eligible workflow selected through authoritative routing context, matching frontmatter, and either non-null approval fields or an exact exemption in an explicitly approved local run configuration.
4. **`skills/agent_skills/<skill-name>/SKILL.md`** - follow reusable task instructions only when a checklist item's **Required Agent Skill** names that exact skill.
5. **`skills/workflows/clientname_project_qaworkflow.md`** - author a new client/project workflow from a non-active template; never use the template directly for a live run.
6. **`docs/MCP.md`** - understand, operate, troubleshoot, and extend the database MCP subsystem.
7. **`docs/SETUP_GUIDE.md`** - install dependencies, configure the local environment, register MCP servers, and verify a new machine.
8. **`ticket_run_config.json`** - inspect the machine-readable shared paths, statuses, formats, and baseline controls.
