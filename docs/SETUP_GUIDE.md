# QA Automation Windows Setup Guide

## 1. Overview

This guide explains how to prepare a completely new Windows device for this QA Automation repository. Follow it from the repository root in Windows PowerShell unless a step says otherwise.

The project coordinates a Jira-driven QA workflow. Its major parts are:

| Part | Responsibility |
|---|---|
| Jira/Atlassian MCP | Retrieves the authoritative Jira issue through the authenticated user's Atlassian permissions. |
| Workflow selection | Matches authoritative client and project metadata to one eligible workflow under `skills/workflows/`. |
| Ticket-run configuration | Defines shared schemas and optional, non-secret, machine-specific run values. |
| Local Python modules | Initialize ticket workspaces, safely download inputs for workflows that permit it, and export saved results. |
| Database MCP execution framework | Exposes profile, connection, metadata, diagnostics, and approved query tools from `MCP/`. |
| Database profiles | Keep database targets and credentials in the ignored `MCP/.env` file rather than source code or ticket artifacts. |
| Ticket artifacts | Keep external inputs under `ticket_runs/<ticket-id>/downloads/`, generated state under `ticket_runs/<ticket-id>/generated/`, logs under `logs/`, and final reports under `output/`. |

The repository commits reusable source code, instructions, workflow definitions, tests, safe examples, and shared configuration. It does not commit the root `.venv`, `MCP/.env`, `ticket_run_config.local.json`, ticket-run contents, logs, final outputs, tokens, passwords, or other machine-specific secrets.

The architecture and both MCP servers are AI-client agnostic. The user needs an MCP-compatible AI client that can configure the required transports, expose tools in an agent-style interaction, and show server status and diagnostics. The repository currently ships a ready-made `.vscode/mcp.json` configuration for VS Code with GitHub Copilot; other clients require an equivalent local configuration in their own format.

## 2. Prerequisites

### Required software and access

| Requirement | Why it is needed | Verification |
|---|---|---|
| Windows 10 or Windows 11 | This guide and the supplied setup scripts use Windows PowerShell paths and commands. | Run `Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion`. |
| Git | Clones the repository and reports branch and working-tree state. | Run `git --version`. |
| MCP-compatible AI client | Connects to local stdio and remote HTTP MCP servers and exposes their tools. | Confirm the client can configure both transports, enter tool-enabled or agent-style mode, and show MCP server status and logs. |
| PowerShell | Runs `MCP/scripts/setup.ps1` and `MCP/scripts/verify.ps1`. | Run `$PSVersionTable.PSVersion`. |
| Python 3.12 | This is the repository's preferred and tested Python version. | Run `py -3.12 --version` after installation. |
| Jira/Atlassian access | Allows the Atlassian MCP server to retrieve authorized Jira issues. | Sign in to the required Atlassian site in a browser and verify the expected Jira project is visible. |
| Database access | Required only when a selected workflow includes live database validation. | Confirm the approved host, database, account, and permissions with the database owner. Do not test with ticket SQL. |
| Network or VPN access | May be required for Atlassian, private repositories, and live databases. | Connect to the approved network or VPN, then use organization-approved connectivity checks. |

The selected AI client must support:

- local stdio MCP servers;
- remote HTTP MCP servers;
- tool-enabled or agent-style interaction; and
- inspection of MCP server status, startup output, and logs.

The repository currently includes a ready-made `.vscode/mcp.json` configuration for VS Code with GitHub Copilot. Users of another MCP-compatible client must translate the same server definitions into that client's configuration format. GitHub Copilot access and its official VS Code extensions are optional client-specific prerequisites only when that example client is used.

SQL Server additionally requires a compatible Microsoft ODBC driver on Windows. The repository defaults to `ODBC Driver 18 for SQL Server` when that connector is selected. PostgreSQL, MySQL, and Snowflake use Python drivers installed from `MCP/requirements.txt`.

### Verify the command locations

Use these checks before creating the environment:

```powershell
Get-Command git
Get-Command powershell
Get-Command py -ErrorAction SilentlyContinue
where.exe python

# Optional check for the tracked VS Code and GitHub Copilot example
Get-Command code -ErrorAction SilentlyContinue
```

If `where.exe python` lists MSYS2, Git, a Windows Store alias, or another unrelated installation before the intended Python, do not rely on bare `python`. Use `py -3.12` to create the environment and then use `.\.venv\Scripts\python.exe` directly.

## 3. Clone And Open The Repository

Choose a short local path when company policy permits it. A path such as `C:\Projects\<repository-folder>` is easier for PowerShell, subprocesses, database drivers, and AI terminal wrappers than a deeply nested OneDrive path.

```powershell
New-Item -ItemType Directory -Path C:\Projects -Force | Out-Null
Set-Location C:\Projects
git clone <repository-url>
Set-Location .\<repository-folder>
# Optional VS Code example
code .
```

Replace `<repository-url>` and `<repository-folder>` with the approved repository values. Do not put credentials or signed URLs in the clone command.

Confirm that the terminal and selected AI client use the repository root, not only the `MCP/` subfolder. When using the tracked VS Code example, also confirm that VS Code opened this root:

```powershell
git status
git branch --show-current
git remote -v
Test-Path .\Basic_Instructions.md
Test-Path .\MCP\server.py
Test-Path .\.vscode\mcp.json
```

The three `Test-Path` commands should return `True`. Confirm that the active branch is the branch your team instructed you to use before making any change.

Every separate clone or separate working-tree folder needs its own `.venv`. Switching branches inside the same working tree normally leaves the existing ignored `.venv` in place, but a second clone does not share it.

Spaces are supported by correctly quoted PowerShell commands, but they increase quoting mistakes. OneDrive can add file synchronization, locks, and delayed timestamps. Very long Windows paths can also exceed limits in terminal wrappers or third-party drivers. These are possible causes to diagnose, not proof that every terminal failure is path-related.

## 4. Python And The Virtual Environment

### 4.1 List installed Python runtimes

The modern Windows Python launcher or Python Install Manager supports:

```powershell
py -0p
```

Look for a Python 3.12 executable. If `py` is not recognized, install the current official Windows Python manager or Python 3.12 distribution, reopen PowerShell, and repeat the check. Do not continue by guessing which bare `python` executable is correct.

### 4.2 Install or select Python 3.12

With the current Python Install Manager:

```powershell
py install 3.12
py -3.12 --version
```

Some devices have the older Python Launcher, which supports `py -3.12` but not `py install`. On those devices, install Python 3.12 through the approved official installer, ensure the launcher is installed, reopen PowerShell, and run `py -0p` and `py -3.12 --version` again.

Expected output is `Python 3.12.x`. A newer major or minor version is not automatically equivalent: compiled drivers and dependency versions may lag behind a new Python release.

### 4.3 Create the root virtual environment

From the repository root:

```powershell
py -3.12 -m venv .venv
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe --version
```

`Test-Path` should return `True`, and the final command should report Python 3.12.

The `.venv` directory is intentionally Git-ignored because it contains machine-specific executables and absolute paths. It will not exist in a fresh clone. An `ENOENT` error mentioning `.venv\Scripts\python.exe` means the MCP client attempted to launch a file that does not exist at that path, usually because setup has not completed or VS Code opened the wrong folder.

Activation is optional. Direct interpreter use is more reliable:

```powershell
.\.venv\Scripts\python.exe -m pip --version
```

To activate it for an interactive terminal:

```powershell
.\.venv\Scripts\Activate.ps1
```

Even after activation, setup and verification commands in this guide use `.\.venv\Scripts\python.exe` explicitly so they cannot silently use another interpreter.

## 5. Install Dependencies

The supported setup entry point is `MCP/scripts/setup.ps1`. It:

1. Resolves the repository root from the script location.
2. Reuses a healthy root `.venv` or replaces a broken one.
3. Prefers Python 3.12 and falls back to another Python 3 runtime only when necessary.
4. Installs `pip>=26.1.2`.
5. Installs database MCP dependencies from `MCP/requirements.txt`.
6. Installs the outer Excel/report dependency from `requirements-e2e.txt`.
7. Verifies the exact `mcp.server.fastmcp.FastMCP` API used by `MCP/server.py` and reports the installed MCP SDK version.

Run it from the repository root:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Unblock-File .\MCP\scripts\setup.ps1
& .\MCP\scripts\setup.ps1
```

`-Scope Process` changes policy only for the current PowerShell process. Closing that terminal discards the change. `Unblock-File` removes the downloaded-file marker from this known repository script; inspect the script before unblocking it.

Expected final output resembles:

```text
MCP version: 1.x.x
FastMCP import OK
Environment ready: ...\.venv\Scripts\python.exe
```

Verify the installed packages:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import importlib.metadata as md; from mcp.server.fastmcp import FastMCP; print('MCP version:', md.version('mcp')); print('FastMCP import OK')"
.\.venv\Scripts\python.exe -c "import openpyxl; print('Excel dependency OK')"
```

Expected: no broken requirements, an MCP `1.x` version, `FastMCP import OK`, and `Excel dependency OK`. The repository intentionally constrains the SDK to `<2` until `MCP/server.py` is deliberately migrated and fully retested against the v2 API.

Do not copy `.venv` from another laptop. Recreate it on each device.

## 6. Current Configuration Model

### 6.1 Shared configuration

`ticket_run_config.json` is committed and reusable. It defines:

- repository-relative ticket, log, and output paths;
- workflow-routing filename conventions;
- run-configuration schemas;
- supported input-acquisition modes;
- stable artifact paths;
- baseline approval checkpoints; and
- MCP ownership boundaries.

It contains no selected demonstration ticket route and no secrets. Do not add a real client, Jira site, ticket, repository, authentication profile, database target, or credential to it.

### 6.2 Safe example

`ticket_run_config.example.json` is a committed placeholder template. It demonstrates the optional local structure using generic or null values.

### 6.3 Optional local configuration

`ticket_run_config.local.json` is optional, machine or run specific, non-secret, and Git-ignored. Create it only when Jira does not provide required routing values, a workflow approval-metadata exemption is authorized, or other required non-secret run values are not supplied by higher-precedence sources:

```powershell
if (-not (Test-Path .\ticket_run_config.local.json)) {
    Copy-Item .\ticket_run_config.example.json .\ticket_run_config.local.json
}
```

Complete only authorized values. The local file requires non-null `configuration_approval.approved_by` and `configuration_approval.approved_on` before the AI may treat it as approved input. Use the exact existing property names and structure from `ticket_run_config.example.json`; do not invent replacement property names. Keep `input_sources` and `database_targets` as empty arrays when those capabilities are unused.

A workflow whose `approved_by` or `approved_on` metadata is `null` is ineligible unless its exact repository-relative path is included in the approved local `workflow_approval.approval_metadata_exempt_workflows` array required by `Basic_Instructions.md`. This exemption makes only that workflow eligible for selection. It does not approve or bypass input selection, context, database execution, write operations, profile switching, report export, or any other workflow checkpoint.

`ticket_run_config.local.json` is optional, local, non-secret, and Git-ignored. Recreate it on every new clone or device when its approved values or workflow exemption are required. It may identify an environment-variable name or MCP profile, but passwords, tokens, cookies, private keys, signed URLs, connection strings, and all other secrets belong only in the ignored `MCP/.env` file or an approved managed-secret system.

Validate only its JSON syntax with:

```powershell
.\.venv\Scripts\python.exe -m json.tool .\ticket_run_config.local.json > $null
if ($LASTEXITCODE -eq 0) { Write-Host 'Local configuration JSON is valid.' }
```

### 6.4 Local configuration field reference

The local file uses the structure below. `null` means that this file does not supply the value and a higher-precedence authoritative source must provide it. An empty array means that the local file declares no entries of that type. Do not replace `null` with guessed text, and do not place illustrative placeholder objects inside an array unless every required field is known and authorized.

```json
{
  "configuration_approval": {
    "approved_by": null,
    "approved_on": null
  },
  "routing": {
    "client_name": null,
    "project_type": null,
    "workflow_variant": null
  },
  "jira": {
    "site_url": null,
    "cloud_id": null,
    "retrieval_mode": "direct_issue",
    "issue_key": null
  },
  "input_sources": [],
  "database_targets": [],
  "workflow_approval": {
    "approval_metadata_exempt_workflows": []
  },
  "required_report_dependencies": []
}
```

Use these general rules:

| Configuration area | When it is compulsory | When it may remain `null` or empty |
|---|---|---|
| `configuration_approval` | Both fields are compulsory whenever `ticket_run_config.local.json` is used. | The entire local file may remain absent when no local values or workflow exemption are required. |
| `routing` | The final resolved run must have `client_name` and `project_type`. | Local values may remain `null` when Jira supplies them. `workflow_variant` remains `null` when no variant applies. The selected workflow validates routing after selection and cannot supply its own selection route. |
| `jira` | The final resolved run needs `issue_key`, `retrieval_mode`, and at least one of `site_url` or `cloud_id`. | Local fields may remain `null` when the user and authorized Atlassian integration supply them during preflight. |
| `input_sources` | Declare entries only when approved local configuration must provide source details not already supplied authoritatively. | Keep `[]` for manual Jira discovery or when Jira and the workflow already identify the sources. |
| `database_targets` | Declare an entry when approved local configuration must identify a database validation target. | Keep `[]` when targets will be obtained from Jira, an approved local input, the selected workflow, or when the workflow does not use databases. |
| `workflow_approval` | Add an exact path only when an authorized local exemption is required for a workflow with null approval metadata. | Keep its array empty for normally approved workflows. |
| `required_report_dependencies` | Add a package name only when the selected workflow requires report software not already supplied by the project environment. | Keep `[]` when no additional dependency is required. |

#### Configuration approval

| Field | Meaning and completion rule |
|---|---|
| `configuration_approval.approved_by` | Actual authorized person or identity that approved the local configuration. It must be non-null when the local file is used; never invent an approver. |
| `configuration_approval.approved_on` | Date of that approval in the approved project format, normally `YYYY-MM-DD`. It must be non-null when the local file is used. |

This approval covers only the non-secret local configuration values. It does not approve the workflow, ticket context, input selection, SQL, profile switch, database write, execution result, or report export.

#### Routing

| Field | Meaning and completion rule |
|---|---|
| `routing.client_name` | Exact client identifier used to select the workflow. Fill it locally only when Jira does not establish it and an authorized person confirms it. The workflow cannot supply the value used to select itself. |
| `routing.project_type` | Exact project identifier used in the workflow filename and metadata, such as an approved EDM, RMS, or POC key. Leave it `null` locally when authoritative Jira metadata supplies it. |
| `routing.workflow_variant` | Optional additional routing discriminator when more than one workflow exists for the same client and project. Leave it `null` when no variant applies. |

The final resolved `client_name` and `project_type` must match the selected workflow filename and frontmatter exactly. Local routing must not override a conflicting Jira value.

#### Jira

| Field | Meaning and completion rule |
|---|---|
| `jira.site_url` | Authorized Jira site URL. Fill it only when the Atlassian integration cannot resolve the intended site and the exact non-secret URL is authorized. |
| `jira.cloud_id` | Authorized Atlassian cloud identifier used instead of or alongside `site_url`. At least one site identifier must exist in the resolved configuration. |
| `jira.retrieval_mode` | Retrieval method permitted by the shared schema. Keep `direct_issue` for the current direct-ticket contract. |
| `jira.issue_key` | Exact ticket key for the run. Leave it `null` locally when the user supplies the key at run start; fill it only when this approved local file is intentionally scoped to one ticket. |

Do not store Atlassian tokens, cookies, authorization headers, or signed attachment URLs in any Jira field.

#### Input sources

`input_sources` describes non-secret acquisition metadata when it must be supplied through approved local configuration. It is not the per-ticket attachment-selection record. Manual include, exclude, defer, and clarification decisions belong in `ticket_runs/<ticket-id>/generated/input_selection.json`, which is created during the applicable workflow.

Keep `input_sources` as `[]` when Jira will discover attachments or links, when the workflow uses manual selection and placement, or when no external input applies. An automatic workflow may use declared sources only when it explicitly permits automatic acquisition and all of its approval and downloader-safety conditions are satisfied.

Documentation-only direct-file example:

```json
{
  "source_type": "direct_file",
  "url": "<authorized-stable-https-url>",
  "authentication_profile": "<optional-profile-name>",
  "credential_environment_variable": "<optional-environment-variable-name>",
  "allowed_extensions": [".<approved-extension>"]
}
```

Documentation-only GitHub-package example:

```json
{
  "source_type": "github_package",
  "repository": "<owner>/<repository>",
  "ref": "<branch-tag-or-commit>",
  "package_path": "<exact/repository/package/path>",
  "authentication_profile": "<optional-profile-name>",
  "credential_environment_variable": "<optional-environment-variable-name>",
  "allowed_extensions": [".<approved-extension>"]
}
```

| Field | Meaning and completion rule |
|---|---|
| `source_type` | Must be `direct_file` or `github_package` under the current schema. It determines which remaining fields are required. |
| `url` | Required only for `direct_file`. Use an authorized stable HTTPS URL without embedded credentials, tokens, or signed query parameters. |
| `repository` | Required only for `github_package`; use the exact `owner/repository` identifier. |
| `ref` | Required only for `github_package`; use the exact authorized branch, tag, or commit. |
| `package_path` | Required only for `github_package`; use the exact package directory, not a similar or parent path. |
| `authentication_profile` | Optional non-secret name of an approved authentication profile. It is not a username, password, or token. |
| `credential_environment_variable` | Optional exact environment-variable name that resolves a credential. Store only the variable name here; the credential value remains outside configuration. |
| `allowed_extensions` | Required for a declared source. List only approved suffixes with leading dots, such as `.md`; never use it to authorize arbitrary content. |

The examples above explain the schema. Do not paste them into the active array with angle-bracket placeholders still present. Use `[]` until every required value is authoritative and the selected workflow permits that source.

#### Database targets

`database_targets` identifies what the QA workflow is allowed to validate. It does not contain database credentials or replace `MCP/.env`. The MCP environment defines how named profiles connect; a database-target entry defines the approved database, schema, source object, and target object for the ticket.

Documentation-only example:

```json
{
  "connection_profile": "<optional-approved-mcp-profile>",
  "db_type": "<approved-connector-type>",
  "database": "<approved-database>",
  "schema": "<approved-schema>",
  "source_object": "<approved-source-object>",
  "target_object": "<approved-target-object>"
}
```

| Field | Meaning and completion rule |
|---|---|
| `connection_profile` | Optional exact MCP profile name approved for this target. Use it when an authorized mapping is needed; never put the profile's credentials here. |
| `db_type` | Required connector type, such as an enabled PostgreSQL or Snowflake connector. It must agree with the approved MCP profile. |
| `database` | Required exact database name containing the validation scope. |
| `schema` | Required exact schema used by the source or target scope. |
| `source_object` | Required authoritative source table, view, or other supported object being validated. |
| `target_object` | Required authoritative transformed or analytics object being validated. |

Leave `database_targets` as `[]` when Jira or an approved downloaded technical document will supply these values during the workflow. After those files are approved and read, the agent records the resolved targets in ticket context, the QA plan, and approval artifacts. If required values remain missing or conflict, the agent must stop and request authorized clarification rather than filling this local file with guesses.

#### Workflow approval exemption

`workflow_approval.approval_metadata_exempt_workflows` contains exact repository-relative paths only for workflows that an authorized local configuration allows to remain eligible while their frontmatter `approved_by` or `approved_on` is `null`.

Keep the array empty for a workflow with normal non-null approval metadata. When an exemption is authorized, add only the exact selected path under `skills/workflows/`. The exemption does not approve any runtime decision and cannot bypass another checkpoint.

#### Required report dependencies

`required_report_dependencies` lists additional software packages that must be available for a workflow's approved report format, for example a Python library required by an existing exporter. It does not contain report inputs, attachment links, report formats, output paths, or approval decisions.

Keep the array empty when the repository environment already provides everything required or when no report is needed. Adding a dependency name does not install it automatically and does not approve report generation.

### 6.5 Resolution order and blockers

The AI must always inspect a present `ticket_run_config.local.json` and validate its configuration approval before declaring routing missing. Routing values use this order:

1. Authoritative Jira ticket context.
2. Explicitly supplied and approved local configuration.
3. Authorized user clarification.
4. Never guess.

The workflow is selected only after routing is resolved; its filename and frontmatter validate the route rather than supplying it. After workflow selection, non-routing values use Jira, the selected eligible workflow, approved local configuration, authorized clarification, and then never guess.

A lower-priority source fills only a value that remains missing. Two conflicting non-empty values block preflight; the agent must report the exact conflict and request authorized clarification. Missing required fields must be listed by their full configuration paths.

**Current limitation:** local configuration merge and validation are instruction-driven. No executable Python resolver currently loads, merges, and enforces Jira context, workflow metadata, and `ticket_run_config.local.json`. The agent must follow the documented rules, but the repository must not claim programmatic enforcement that does not yet exist.

## 7. Input Acquisition Model

The shared framework supports both `manual` and `automatic` input acquisition. `ticket_run_config.json` sets no global default. Every selected workflow must explicitly declare its mode.

The current POC workflow declares manual acquisition only for that POC. Its agent must discover Jira attachments and links, present a proposed input list, receive per-item decisions and explicit selection approval, instruct the authorized user where to place approved files, pause, and then verify the files locally. It must not invoke the downloader.

Automatic downloader functionality remains present in `modules/download_ticket_inputs.py`. A future workflow may explicitly select automatic acquisition only when it provides permission, required acquisition approvals are satisfied, authentication is configured, and downloader safety controls are active. The existence of downloader code does not authorize a workflow to call it.

## 8. MCP Environment Configuration

### 8.1 Create the ignored environment file

The safe example is `MCP/.env.example`. The real local file is `MCP/.env`:

```powershell
if (-not (Test-Path .\MCP\.env)) {
    Copy-Item .\MCP\.env.example .\MCP\.env
}
Test-Path .\MCP\.env
git check-ignore .\MCP\.env
```

`Test-Path` should return `True`. `git check-ignore` should print `MCP/.env`, confirming that Git ignores the local file. Never commit `MCP/.env`.

### 8.2 Active connector and named profiles

The top-level `DB_TYPE`, `DB_HOST`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`, `DB_CONNECTION_OPTIONS`, `DB_TIMEOUT_SECONDS`, and `DB_MAX_ROWS` values define the connector active when the MCP process starts.

`DB_ACTIVE_PROFILE` names the active profile. `DB_PROFILES_JSON` is a one-line JSON object keyed by exact profile names. Profile names are normalized to lowercase by the service, but workflows and approvals should use the configured name consistently rather than relying on normalization.

Supported profile fields are:

```json
{
  "db_type": "<connector-type>",
  "host": "<host-or-account>",
  "database": "<database>",
  "username": "<username>",
  "password": "<password>",
  "connection_options": {},
  "timeout_seconds": 30,
  "max_rows": 500
}
```

The actual `.env` value must remain valid one-line JSON. Do not leave angle-bracket placeholders in a profile that will be selected.

### 8.3 Profiles represented in the example

`MCP/.env.example` currently includes:

- **Demo:** offline deterministic connector for setup and smoke tests.
- **PostgreSQL:** host, database, username, password, and `connection_options.port`.
- **MySQL:** host, database, username, password, and `connection_options.port`.
- **Snowflake:** placeholder-only account, database, username, password, warehouse, schema, role, and authenticator fields.

The code also supports SQL Server, but `MCP/.env.example` does not currently contain a ready-made SQL Server profile. SQL Server setup additionally requires the appropriate ODBC driver and an approved profile created for the target environment.

For Snowflake, the example maps fields as follows:

| Profile field | Connector use |
|---|---|
| `db_type: snowflake` | Selects the Snowflake connector. |
| `host` | Becomes the Snowflake `account` identifier. Use an account identifier, not a URL or `.snowflakecomputing.com` hostname. |
| `database` | Becomes the default Snowflake database when supplied. |
| `username` | Becomes the Snowflake `user` and is required by current validation. |
| `password` | Password placeholder in the example; the real secret belongs only in ignored or managed secret configuration. |
| `connection_options.warehouse` | Forwarded to the Snowflake driver. |
| `connection_options.schema` | Extracted and passed as the session schema. |
| `connection_options.role` | Forwarded to the Snowflake driver. |
| `connection_options.authenticator` | Forwarded to the Snowflake driver when applicable. |

The current example does not add private-key settings because the repository connector does not explicitly implement a private-key configuration contract.

### 8.4 Profile operations through MCP

After starting `mcp-execution-framework`, invoke the exposed MCP tools through the configured AI client:

1. Call `tool_list_connection_profiles` and inspect `ready`, `issues`, and `active` without exposing secrets.
2. After changing `MCP/.env`, request approval and call `tool_reload_configuration(confirm=true)`.
3. Select the exact intended profile. First surface the confirmation requirement, then call `tool_switch_connection_profile(name="<profile-name>", confirm=true)` only after explicit approval.
4. Call `tool_test_connection` for the approved target.
5. Compare returned safe metadata with the approved environment and database mapping.

Never assume the currently active profile is the intended profile. A successful profile listing is not a successful connection test, and a successful connection test is not approval to execute ticket SQL.

## 9. Configure The MCP Servers

### 9.1 Generic MCP client requirements

Any supported AI client must configure and verify these two MCP connections. The repository does not currently ship configuration files for clients other than the VS Code example, so use the chosen client's documentation to translate these definitions without changing their meaning.

**Local database execution server**

- **Server name:** `mcp-execution-framework`
- **Transport:** stdio
- **Command:** the repository interpreter at `.\.venv\Scripts\python.exe`
- **Script argument:** `MCP/server.py`
- **Working directory:** `MCP`
- **Environment source:** `MCP/.env`, loaded by the server configuration layer

The client must launch that command from the same repository clone, keep stdio connected, discover the exposed tools, and provide access to current startup output or diagnostics.

**Atlassian server**

- **Server name in the tracked example:** `atlassian-mcp-server`
- **Transport:** remote HTTP
- **Endpoint:** `https://mcp.atlassian.com/v1/mcp/authv2`, as defined in the current repository's `.vscode/mcp.json`
- **Authentication:** authorized Atlassian authentication completed through the selected client's supported flow

Do not copy OAuth tokens, cookies, or organization-specific URLs into repository files. Client commands, menu names, authentication prompts, and log locations vary. After configuration, verify that both servers are running, the local server exposes 12 tools, and the authenticated Atlassian connection can access only the intended resources.

### 9.2 VS Code and GitHub Copilot example

The tracked `.vscode/mcp.json` defines two servers:

- `atlassian-mcp-server`, an HTTP Atlassian MCP connection;
- `mcp-execution-framework`, a local stdio server.

The local entry uses:

```text
${workspaceFolder}\.venv\Scripts\python.exe
${workspaceFolder}\MCP\server.py
${workspaceFolder}\MCP
```

For this client-specific example, VS Code must open the repository root and `.venv` must exist there. After creating or replacing `.venv`, use **Developer: Reload Window** or close and reopen VS Code so MCP discovery uses the new interpreter.

To start the servers in VS Code with GitHub Copilot:

1. Press `Ctrl+Shift+P`.
2. Run **MCP: List Servers**.
3. Select `mcp-execution-framework` and choose **Start Server**.
4. Select `atlassian-mcp-server` and choose **Start Server**.
5. Complete Atlassian browser authentication when prompted.
6. Open **View > Output**.
7. Select the relevant MCP output channel and check the newest timestamps rather than relying on old messages.

The local server logs:

```text
MCP Server started. Waiting for connections...
```

The current `MCP/server.py` registers 12 tools, so successful client discovery should report:

```text
Discovered 12 tools
```

If the count changes in future code, trust the current registered tool surface and update this guide deliberately.

A manual startup diagnosis is:

```powershell
.\.venv\Scripts\python.exe .\MCP\server.py
```

The process should wait for stdio input. Press `Ctrl+C` to stop it before starting the same server through the configured AI client. In the tracked example, start it through VS Code after stopping the manual process.

## 10. Atlassian And Jira Setup

Cloning this repository does not copy Atlassian authentication, OAuth grants, or site-level MCP installation state. Each user or device must configure the Atlassian MCP server in the selected AI client and authenticate with an account that can access the intended Jira site. The first successful connection to a site may also install the Atlassian MCP app through the OAuth consent flow. After that site-level installation exists, other authorized users normally need only their own OAuth consent.

1. Start the configured Atlassian MCP connection through the AI client's server controls.
2. Complete the supported OAuth flow with the account authorized for the required Jira site, explicitly selecting the intended site and Jira access when prompted.
3. Return to the AI client and confirm the server is running.
4. Confirm that Atlassian resource discovery returns the intended site rather than an empty list.
5. In the AI client's tool-enabled or agent mode, ask the agent to retrieve a placeholder ticket such as `$TicketKey` by exact key through the configured Atlassian MCP.
6. Confirm that the returned issue belongs to the expected authorized site before proceeding.

For the tracked VS Code and GitHub Copilot example, use **MCP: List Servers** to start `atlassian-mcp-server`, complete the browser authentication prompt, and use Copilot Agent mode for the retrieval request.

Jira is authoritative for the business request and routing metadata it actually contains. A Jira hyperlink, attachment name, or repository reference is only a reference. Its content has not been inspected until an authorized process retrieves it or an authorized user places the approved file locally and the workflow verifies it.

`canceled: canceled` normally means the client canceled or closed the MCP request or server session; it does not mean the Jira issue was canceled. If Atlassian MCP stops:

1. Open the AI client's MCP server controls.
2. Restart `atlassian-mcp-server`.
3. Reauthenticate if requested.
4. Check fresh client output or diagnostic timestamps.
5. Retry direct issue retrieval in the same AI-client conversation or session.

In the tracked VS Code example, the equivalent controls are **MCP: List Servers** and **View > Output**; the retry may remain in the same Copilot chat.

Do not restart the entire ticket workflow or create duplicate artifacts merely because the transport restarted. First determine the last durable workflow checkpoint.

## 11. Verification Checklist

Run these from the repository root.

### Python and environment

```powershell
py -3.12 --version
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe --version
```

Expected: Python 3.12 is available, `Test-Path` returns `True`, and the direct interpreter reports Python 3.12.x.

### Dependencies

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import importlib.metadata as md; from mcp.server.fastmcp import FastMCP; print('MCP version:', md.version('mcp')); print('FastMCP import OK')"
.\.venv\Scripts\python.exe -c "import openpyxl; print('Excel dependency OK')"
```

Expected: no broken dependency report, an MCP `1.x` version, `FastMCP import OK`, and `Excel dependency OK`.

### Setup and local configuration

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Unblock-File .\MCP\scripts\setup.ps1
& .\MCP\scripts\setup.ps1
Test-Path .\MCP\.env
git check-ignore .\MCP\.env
```

Expected: setup reports the environment path, `Test-Path` returns `True`, and `git check-ignore` prints `MCP/.env`.

### MCP startup

Start both servers through the configured AI client's MCP controls. Verify that the local server starts and that the client discovers 12 tools; exact status and discovery wording varies by client.

For the tracked VS Code and GitHub Copilot example, use **MCP: List Servers** to start both servers and **View > Output** to confirm fresh output includes:

```text
MCP Server started. Waiting for connections...
Discovered 12 tools
```

### Profiles and connection

In the AI client's tool-enabled or agent mode:

```text
Call tool_list_connection_profiles. Do not reveal secrets and do not switch profiles.
```

After explicit selection and any required switch approval:

```text
Call tool_test_connection for the approved profile and database. Do not execute ticket SQL.
```

Expected: the intended profile is active, `ready` is true, and the connection result safely identifies the approved target.

### Ticket workspace initialization

Use a non-production placeholder key in a setup-only environment:

```powershell
$TicketKey = 'YOUR-TICKET-KEY'
.\.venv\Scripts\python.exe -m modules.init_ticket_run $TicketKey
```

Expected: `ticket_runs/<ticket-id>/downloads/`, `ticket_runs/<ticket-id>/generated/`, starter generated artifacts, and `logs/<ticket-id>.log` exist. Do not initialize a real demonstration ticket until preflight succeeds.

### Test suite

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Unblock-File .\MCP\scripts\verify.ps1
& .\MCP\scripts\verify.ps1
```

Expected final message:

```text
All verification gates passed.
```

The script compiles tracked Python files, runs MCP tests, performs an offline demo smoke test, and runs outer helper tests. Normal tests do not require live Jira or database access.

## 12. Troubleshooting

### 12.1 `spawn .venv\Scripts\python.exe ENOENT`

- **Symptom:** The configured AI client cannot start `mcp-execution-framework` and reports `ENOENT`.
- **Likely cause:** `.venv` is absent, broken, or located outside the opened workspace.
- **Diagnosis:** Run `Test-Path .\.venv\Scripts\python.exe` and inspect the selected client's local stdio server definition. For the tracked VS Code example, inspect `.vscode/mcp.json`.
- **Safe fix:** Open the repository root, run `MCP/scripts/setup.ps1`, then restart or reload the AI client. In VS Code, use **Developer: Reload Window**.
- **Stop and ask for help:** If the interpreter exists but the client still resolves a different workspace path.

### 12.2 `Test-Path` returns `False`

- **Symptom:** The virtual-environment interpreter check fails.
- **Likely cause:** Fresh clone, failed environment creation, wrong current directory, or deleted `.venv`.
- **Diagnosis:** Run `Get-Location`, `Test-Path .\MCP\scripts\setup.ps1`, and `py -0p`.
- **Safe fix:** Change to the repository root and rerun the setup script.
- **Stop and ask for help:** If security software repeatedly removes or blocks the interpreter.

### 12.3 Wrong Python version

- **Symptom:** Setup uses an unexpected runtime or a dependency fails to install.
- **Likely cause:** Python 3.12 is absent or another runtime appears first.
- **Diagnosis:** Run `py -0p`, `py -3.12 --version`, and `.\.venv\Scripts\python.exe --version`.
- **Safe fix:** Install Python 3.12 and recreate `.venv` through the setup script.
- **Stop and ask for help:** Before deleting an environment containing uncommitted local tooling or when corporate software policy controls Python installation.

### 12.4 Bare `python` resolves to MSYS2 or another installation

- **Symptom:** Paths or package locations mention MSYS2, Git, the Store alias, or an unrelated Python.
- **Likely cause:** `PATH` order differs from the intended runtime.
- **Diagnosis:** Run `where.exe python` and `Get-Command python -All`.
- **Safe fix:** Use `py -3.12` to create `.venv`, then use `.\.venv\Scripts\python.exe` directly.
- **Stop and ask for help:** Before changing organization-managed system `PATH` entries.

### 12.5 `setup.ps1` is blocked or shows an unsigned-script warning

- **Symptom:** PowerShell refuses to run the setup script.
- **Likely cause:** Execution policy or a downloaded-file marker.
- **Diagnosis:** Run `Get-ExecutionPolicy -List` and `Get-Item .\MCP\scripts\setup.ps1 -Stream *`.
- **Safe fix:** Inspect the script, then run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and `Unblock-File .\MCP\scripts\setup.ps1`.
- **Stop and ask for help:** If organization policy prevents process-scoped execution or the script content differs from the approved repository.

### 12.6 Missing `MCP/.env`

- **Symptom:** Reload reports that local configuration was not found, or startup lacks required values.
- **Likely cause:** `.env` is intentionally absent from a fresh clone.
- **Diagnosis:** Run `Test-Path .\MCP\.env`.
- **Safe fix:** Copy `MCP/.env.example` to `MCP/.env`, then replace only approved placeholders locally.
- **Stop and ask for help:** If you do not know which profiles or secrets are authorized.

### 12.7 `DB_TYPE is required`

- **Symptom:** MCP configuration validation fails at startup or reload.
- **Likely cause:** `DB_TYPE` is missing or was cleared from `MCP/.env`.
- **Diagnosis:** Inspect only the non-secret key name in `MCP/.env`; do not print the whole file in shared output.
- **Safe fix:** Restore an approved connector type such as `demo`, `postgresql`, `mysql`, `snowflake`, or `sqlserver`.
- **Stop and ask for help:** If the required target connector is unknown.

### 12.8 `DB_HOST is required`

- **Symptom:** A non-demo profile fails validation.
- **Likely cause:** The selected profile lacks `host` or contains an unresolved placeholder.
- **Diagnosis:** Call `tool_list_connection_profiles` and inspect safe `issues` and presence flags.
- **Safe fix:** Obtain the exact authorized host or Snowflake account identifier and update only local secret-backed configuration.
- **Stop and ask for help:** Never infer a host from another environment or ticket.

### 12.9 Stale MCP log timestamps

- **Symptom:** Output appears to show an old success or failure after a restart.
- **Likely cause:** The client output or diagnostics retain previous server sessions.
- **Diagnosis:** Compare timestamps and trigger one harmless current action such as profile listing.
- **Safe fix:** Clear or reopen the client's diagnostics and read only fresh entries from the current start attempt. In VS Code, use **View > Output**.
- **Stop and ask for help:** If the client cannot identify which server instance produced the output.

### 12.10 Local MCP starts and exits

- **Symptom:** The server process closes immediately.
- **Likely cause:** Configuration validation, missing dependency, incorrect working directory, or closed stdio transport.
- **Diagnosis:** Run `.\.venv\Scripts\python.exe .\MCP\server.py` and inspect the safe error text.
- **Safe fix:** Correct the reported local setup problem, stop the manual process, and restart through the configured AI client.
- **Stop and ask for help:** For unexplained tracebacks, repeated crashes, or any error containing sensitive material.

### 12.11 `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`

- **Symptom:** `MCP/server.py` exits during startup because `mcp.server.fastmcp` cannot be imported, even though `pip check` and `import mcp` succeed.
- **Likely cause:** A fresh environment installed MCP Python SDK v2. The current server deliberately uses the maintained v1 `mcp.server.fastmcp.FastMCP` API, so `MCP/requirements.txt` must retain its `<2` upper bound until a planned v2 migration is implemented and tested.
- **Why shallow checks pass:** `pip check` validates dependency metadata, while `import mcp` verifies only the package root. Neither proves that the exact API imported by `MCP/server.py` exists.
- **Diagnosis:** Run `.\.venv\Scripts\python.exe -c "import importlib.metadata as md; print(md.version('mcp'))"`, then run `.\.venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('FastMCP import OK')"`.
- **Safe fix:** Confirm `MCP/requirements.txt` contains `mcp>=1.28.0,<2`, then rerun `MCP/scripts/setup.ps1`. The setup script repairs the environment and now fails unless the exact FastMCP import succeeds.
- **Verification:** The setup output reports an MCP `1.x` version and `FastMCP import OK`; manual startup remains running without this traceback; the MCP client then discovers 12 tools.
- **Stop and ask for help:** Do not replace the import with `MCPServer` as a one-line fix. MCP SDK v2 requires an intentional server migration and complete regression testing.

### 12.12 VS Code/Copilot tool exposure and Atlassian access

#### Too many selected tools

- **Symptom:** MCP tools are visible and checked in VS Code, but Copilot Agent Mode reports that required profile-management, Jira, or execution tools are unavailable.
- **Likely cause:** A very large active tool set can cause required tools to be omitted from the agent's effective context even though the interface shows them as selected. One observed run had approximately 173 selected tools; this is an observation, not a guaranteed numeric limit.
- **Diagnosis:** Open the tool picker and review the total selected tool set before assuming an MCP server or its implementation is broken. A checked tool is not proof that the current agent conversation can invoke it.
- **Safe fix:** Deselect unrelated tools. Keep only the tools required by the selected workflow, including the relevant QA Automation, Atlassian, and database MCP tools. Start a fresh agent conversation after reducing the tool set so tool discovery is rebuilt.
- **Verification:** Ask for a harmless metadata operation, such as listing secret-safe database profiles or Atlassian resources, and confirm that the previously unavailable tool is callable before resuming the workflow.

#### Duplicate Atlassian MCP entries

- **Symptom:** Jira authentication behaves inconsistently, one Atlassian server succeeds while another fails, or the agent invokes a different Atlassian connection from the one the user authorized.
- **Likely cause:** A global Atlassian MCP installation and the repository's workspace-specific Atlassian MCP entry are both active. Separate entries do not necessarily share OAuth state, cached tools, or site authorization.
- **Diagnosis:** In VS Code, run **MCP: List Servers** and identify each Atlassian entry and its configuration source. The tracked workspace entry is `atlassian-mcp-server` in `.vscode/mcp.json` and uses `https://mcp.atlassian.com/v1/mcp/authv2`. Check fresh output timestamps for the exact entry the agent is expected to use.
- **Safe fix:** Keep one intended Atlassian entry active for the run and stop or disable the duplicate. A user may give the workspace entry a clearer non-ticket-specific local display name when their client supports aliases, but shared repository configuration must remain reusable. Complete OAuth through the same entry the agent will invoke, then start a fresh agent conversation.
- **Verification:** Confirm that Jira retrieval and accessible-resource discovery are both executed through the intended workspace entry.

#### OAuth succeeds but resources are empty or forbidden

- **Symptom:** Authentication appears to complete, but resource discovery returns `[]`, Jira requests return `403 Forbidden`, direct issue retrieval reports `The app is not installed on this instance`, or authorization errors continue.
- **Likely cause:** The account identity is authenticated, but the selected MCP entry has incomplete, stale, or wrong-site OAuth authorization. The Atlassian MCP app may also be absent from the intended site or blocked by organization policy.
- **Diagnosis:** Confirm that the same Atlassian account can open the intended Jira site directly. Inspect fresh diagnostics from the one active Atlassian MCP entry and confirm its endpoint. Do not treat successful account identification as proof of Jira-site authorization.
- **Safe fix:** Stop duplicate Atlassian entries. Reset or revoke the failed authorization, restart the intended workspace entry, explicitly select the intended Jira site and Jira access during OAuth, and start a fresh agent conversation. When this is the site's first MCP connection or user-installed apps are restricted, an authorized site administrator must complete or permit the consent flow. In Atlassian Administration, review **Apps > Sites > [site] > Connected apps > Settings** and **Rovo > Rovo MCP server** permissions.
- **Verification:** Accessible-resource discovery returns the intended site and direct read-only issue retrieval succeeds.

#### Exact Atlassian cloud ID

- **Symptom:** Jira retrieval fails when supplied only a site name, browser URL, or assumed identifier even though authentication otherwise works.
- **Likely cause:** The Jira MCP operation requires the exact Atlassian cloud ID for the authorized site. A site name or issue browse URL is not the cloud ID.
- **Safe fix:** Retrieve the exact cloud ID from Atlassian's accessible-resource response and reuse that returned identifier for direct issue operations. If the accessible-resource response is empty, repair OAuth or site-app authorization first. Never guess, derive, or hardcode a cloud ID from the Jira URL, and do not place a client-specific cloud ID in shared repository files.
- **Verification:** Direct retrieval succeeds using the verified cloud ID and exact issue key.

#### Cancellation or stopped server

- **Symptom:** Jira retrieval ends with `canceled: canceled` or the Atlassian server stops.
- **Likely cause:** The client canceled the transport, authentication expired, or the server session stopped. This does not mean the Jira issue was canceled.
- **Safe fix:** Restart only the intended Atlassian server, reauthenticate if requested, inspect fresh output, and retry the read-only retrieval in the same workflow state. Do not repeat completed ticket acquisition or create duplicate artifacts.

Authentication and cached tool state are client- and server-entry-specific. Reauthenticating a different MCP entry, IDE profile, AI client, or browser account does not refresh the connection used by the agent. Never copy OAuth tokens or cookies between devices or store them in repository files. Stop and ask for help if the user cannot authorize the app, organization policy blocks the required client or Jira permissions, or direct retrieval still fails after an authorized administrator completes consent.

### 12.13 AI client returns no response

- **Symptom:** Tool-enabled or agent mode ends without a useful response. One observed GitHub Copilot message is `Sorry, no response was returned`.
- **Likely cause:** Tool timeout, canceled MCP request, client extension failure, or malformed terminal-runner invocation.
- **Diagnosis:** Inspect the client's MCP output or diagnostics, terminal exit status, MCP tool-call history, and durable ticket artifacts before retrying.
- **Safe fix:** Restart only the failed server or retry the read-only step. Do not repeat a write or query unless its previous execution status is known.
- **Stop and ask for help:** When an approval-gated or write action may already have executed.

### 12.14 AI client terminal-runner quoting or escaping failure

- **Symptom:** A command works when typed manually but fails through the AI client's terminal runner with broken quotes or paths. GitHub Copilot's terminal wrapper is one known example of this general client capability.
- **Likely cause:** Nested quoting, unescaped backslashes, spaces, or terminal-runner serialization.
- **Diagnosis:** Compare the exact displayed command with the documented PowerShell command and run a harmless path check manually.
- **Safe fix:** Use repository-relative paths, single quotes for literal PowerShell values, and direct interpreter invocation. Break long commands into safe steps.
- **Stop and ask for help:** Before simplifying a command in a way that would expose a secret or remove a safety option.

### 12.15 Long OneDrive path

- **Symptom:** Subprocesses, temporary files, or wrappers fail only in a deeply nested synchronized folder.
- **Likely cause:** Path length, synchronization locks, or quoting complexity may be contributing.
- **Diagnosis:** Inspect `Get-Location`, path length, and whether the same harmless command works from a short approved clone.
- **Safe fix:** Create a separate clone under a short path such as `C:\Projects\<repository-folder>` when policy permits, then create a new `.venv` there.
- **Stop and ask for help:** Before moving a working tree with uncommitted changes or restricted data.

### 12.16 Command works manually but not through the AI client

- **Symptom:** Manual PowerShell succeeds while the AI client invocation fails. GitHub Copilot is one client in which this difference may be observed.
- **Likely cause:** Different working directory, environment variables, shell, interpreter, permissions, or quoting.
- **Diagnosis:** Compare `Get-Location`, `$env:PATH`, interpreter path, and the exact command without printing secret values.
- **Safe fix:** Configure the AI client to use the repository root and the explicit `.venv` interpreter, then retry a non-destructive check.
- **Stop and ask for help:** If success depends on passing a credential through chat or command history.

### 12.17 Local terminal execution versus MCP tool execution

- **Symptom:** Running `server.py` or a database client manually is mistaken for an MCP tool call.
- **Likely cause:** The two execution paths use different transports and approval boundaries.
- **Diagnosis:** Confirm whether the action appears in MCP tool-call history and structured MCP output.
- **Safe fix:** Use manual startup only for diagnosis. Perform workflow database operations through approved MCP tools.
- **Stop and ask for help:** If execution evidence cannot prove which path ran the statement.

Terminal execution and MCP tool execution are separate AI-client capabilities. A failure in an AI client's terminal runner does not prove that the MCP server or project code is broken; diagnose each path independently.

### 12.18 Interactive Python prompt opened accidentally

- **Symptom:** The terminal shows `>>>` and PowerShell commands fail as Python syntax.
- **Likely cause:** Python was launched without `-m` or `-c` arguments.
- **Diagnosis:** Look for the `>>>` prompt.
- **Safe fix:** Type `exit()` and press Enter. On Windows, `Ctrl+Z` followed by Enter also exits the Python prompt.
- **Stop and ask for help:** If a script remains running or the terminal contains an unfinished sensitive command.

### 12.19 Profile exists but demo remains active, or the profile name mismatches

- **Symptom:** Listing shows the intended profile, but `active` remains on demo or switching reports unknown profile.
- **Likely cause:** The profile was not explicitly switched, the configuration was not reloaded, or the name differs.
- **Diagnosis:** Call `tool_list_connection_profiles` and compare the exact approved name.
- **Safe fix:** Reload after approval, request profile-switch approval, switch using the exact name, and test the connection.
- **Stop and ask for help:** If multiple profiles could match the approved target or metadata conflicts.

### 12.20 Connection test hangs or times out

- **Symptom:** `tool_test_connection` does not return within the configured timeout.
- **Likely cause:** Database service, DNS, firewall, VPN, driver, authentication, or target mismatch.
- **Diagnosis:** Confirm the approved host, VPN state, local service status where applicable, and configured timeout without printing secrets.
- **Safe fix:** Restore required network/service access and repeat only the connection test.
- **Stop and ask for help:** Do not increase timeouts indefinitely or execute SQL to diagnose an unverified target.

### 12.21 Local database service or VPN is unavailable

- **Symptom:** Connection is refused, host is unreachable, or authentication cannot reach the server.
- **Likely cause:** Local service stopped, company network unavailable, or VPN disconnected.
- **Diagnosis:** Use organization-approved service and connectivity checks; verify VPN status.
- **Safe fix:** Start the authorized local service or reconnect the approved VPN, then retest the connection.
- **Stop and ask for help:** If starting the service requires administrator access or the target network is unclear.

### 12.22 Windows `PytestCacheWarning`

- **Symptom:** Tests pass but pytest warns that `.pytest_cache` could not be created or written.
- **Likely cause:** OneDrive, permissions, antivirus, or another process holds the cache path.
- **Diagnosis:** Confirm the actual passed/failed totals and inspect the warning path.
- **Safe fix:** Use the repository verification script, which uses an isolated system temporary directory, or run pytest with an approved `--basetemp` outside the synchronized tree.
- **Stop and ask for help:** If tests fail, temporary files cannot be cleaned safely, or the warning affects actual results.

### 12.23 Jira link discovered but content was not inspected

- **Symptom:** The agent knows a URL or attachment name but lacks file content.
- **Likely cause:** Discovery is not acquisition, and protected sources may require user access.
- **Diagnosis:** Check `input_selection.json` and the ticket `downloads/` inventory.
- **Safe fix:** Follow the selected workflow's acquisition mode. For the current POC, obtain selection approval and have an authorized user place the approved file locally.
- **Stop and ask for help:** Never invent the linked content or request credentials in chat.

### 12.24 Word and Excel manual-local-input limitation

- **Symptom:** A remote Word or Excel link is available, but the POC agent cannot treat it as inspected.
- **Likely cause:** The current POC requires authorized manual placement and local verification.
- **Diagnosis:** Confirm whether the approved original file exists under `ticket_runs/<ticket-id>/downloads/`.
- **Safe fix:** Have the authorized user place the approved file locally. Do not open macros or execute embedded content.
- **Stop and ask for help:** For unsupported formats, password-protected files, macros, or unexpected files.

### 12.25 Automatic downloader is present but unavailable to the POC

- **Symptom:** `modules/download_ticket_inputs.py` exists, but the POC workflow forbids calling it.
- **Likely cause:** Acquisition permission belongs to the selected workflow, not to the module's presence.
- **Diagnosis:** Read the selected workflow's `input_acquisition.mode` and acquisition steps.
- **Safe fix:** Follow manual selection and placement for the current POC. Use automatic downloading only in a separately approved workflow that explicitly permits it and satisfies all controls.
- **Stop and ask for help:** If workflow mode is missing, conflicting, or ambiguous.

### 12.26 Instruction-driven configuration limitation

- **Symptom:** A local JSON file is syntactically valid, but no Python command automatically proves the merged run configuration.
- **Likely cause:** The executable configuration resolver has not yet been implemented.
- **Diagnosis:** Compare Jira, workflow, local configuration, and clarification sources using the documented precedence.
- **Safe fix:** Have the agent report every resolved value, source, conflict, and missing field during read-only preflight.
- **Stop and ask for help:** Whenever sources conflict or the agent cannot prove the selected route or target.

### 12.27 Pending Windows canonical-path issue in `modules/download_ticket_inputs.py`

**Future reliability fix not yet applied.**

- **Symptom:** A downloader destination may behave differently under Windows canonical path, junction, reparse-point, case, or alias handling than its displayed path suggests.
- **Likely cause:** Windows path canonicalization has edge cases beyond ordinary lexical path checks.
- **Diagnosis:** Compare `Resolve-Path`, `Get-Item -Force`, link/reparse metadata, and the intended repository root without downloading or extracting content.
- **Safe fix:** Do not work around the check or relax path validation. Use a simple local repository path with no junctions for an approved test and record the limitation for the future code fix.
- **Stop and ask for help:** If any source, staging, extraction, or destination path cannot be proven to remain inside the intended ticket workspace.

## 13. Security And Safety

- Keep secrets only in approved ignored environment files or managed secret systems. Verify ignore behavior with `git check-ignore` and review `git status` before every commit.
- Never put credentials in `ticket_run_config.json`, `ticket_run_config.example.json`, `ticket_run_config.local.json`, Jira, prompts, workflows, ticket artifacts, logs, reports, screenshots, or commands shared with others.
- List profiles safely, select the exact profile explicitly, and test the connection before metadata or query work.
- Prefer read-only validation. Every DDL, DML, setup command, or other write needs separate explicit authorization. Read-only approval never grants write approval.
- Execute one approved statement per MCP request. Do not bypass SQL guard, profile-switch confirmation, context approval, or execution approval.
- Do not fabricate Jira content, downloaded content, database objects, expected outcomes, execution evidence, or approvals.
- Treat local inputs as untrusted. Preserve original files, do not execute downloaded SQL automatically, do not open macros, and do not extract archives outside approved safe handling.
- Reject or escalate archive traversal, absolute paths, drive-qualified paths, symbolic links, unsafe Windows names, suspicious expansion ratios, and any destination that could leave the ticket workspace.
- Do not read an unexpected local file until the user explicitly decides whether to include it.
- Redact tokens, passwords, cookies, signed query strings, connection details, and sensitive error data from logs and generated artifacts.
- Store workflow logs only under `logs/<ticket-id>.log` and final reports only under `output/<ticket-id>/`.

## 14. Final New-Device Checklist

- [ ] Clone the approved repository into a short, trusted local path.
- [ ] Open the repository root in the selected MCP-compatible AI client and confirm the instructed branch.
- [ ] Read `Basic_Instructions.md` completely.
- [ ] Install or select Python 3.12 and verify it with `py -3.12 --version`.
- [ ] Create the root `.venv` and confirm `.\.venv\Scripts\python.exe` exists.
- [ ] Run `MCP/scripts/setup.ps1` with process-scoped execution policy.
- [ ] Verify the exact `mcp.server.fastmcp.FastMCP` and `openpyxl` imports, confirm the MCP SDK is `1.x`, and run `pip check`.
- [ ] Copy `MCP/.env.example` to ignored `MCP/.env`.
- [ ] Configure only approved local database profiles and keep secrets out of Git.
- [ ] Create approved `ticket_run_config.local.json` only when non-secret run values are genuinely needed.
- [ ] Restart or reload the AI client and start `mcp-execution-framework` and the configured Atlassian MCP server.
- [ ] Keep only one intended Atlassian MCP entry active and stop or disable duplicate global or workspace entries.
- [ ] Limit the selected agent tools to those required for the current workflow, then start a fresh agent conversation.
- [ ] Confirm fresh local MCP startup output and discovery of 12 tools.
- [ ] Authenticate Atlassian, confirm resource discovery lists the intended site, and verify direct read-only access to an issue on that site.
- [ ] List profiles, explicitly select the intended profile, and test its connection without executing ticket SQL.
- [ ] Run `MCP/scripts/verify.ps1` and confirm every gate passes.
- [ ] Start the ticket only after read-only preflight can prove routing, workflow eligibility, configuration, tools, and dependencies.
- [ ] Follow the selected workflow's acquisition mode and every human approval gate.
- [ ] Preserve real evidence and stop whenever context, configuration, target, approval, or execution status is uncertain.

For the tracked VS Code configuration, use GitHub Copilot Agent mode and **MCP: List Servers**.
