# Add Agent Skills

## Purpose

Agent skills provide reusable instructions, procedures, templates, and supporting resources that an AI agent can use while completing repository workflows.

In this repository, agent skills are stored under:

`skills/agent_skills/`

Workflow files are stored separately under:

`skills/workflows/`

Do not place workflow files inside `skills/agent_skills/`, and do not place reusable skill packages inside `skills/workflows/`.

---

## Where Agent Skills Can Be Found

Agent skills may come from approved sources such as:

- skill catalogues such as `skills.sh`;
- the original GitHub repository linked by a skill catalogue;
- official repositories maintained by the skill author or vendor;
- trusted open-source repositories;
- internal company repositories;
- skills created and reviewed by the project team.

A catalogue page should be treated as a discovery source. Before adding a skill, open the original repository linked by the catalogue and review the actual skill files there.

Do not add a skill only because its title or description appears relevant.

---

## Review the Skill Before Adding It

Before copying an external skill into this repository, verify:

1. The original repository and author are identifiable.
2. The skill matches the intended use case.
3. The licence permits its use.
4. The skill does not request passwords, tokens, private keys, or other secrets.
5. The skill does not instruct the agent to bypass approval gates or repository safety rules.
6. The skill does not contain unexplained executables, binaries, macros, remote-download commands, or write operations.
7. The skill does not conflict with `Basic_Instructions.md` or the selected workflow.
8. All files referenced by the skill are available.

Treat every external skill as untrusted until it has been reviewed.

Repository-level instructions and approved workflow rules always take priority over imported skill instructions.

---

## Manual Installation

### Step 1: Find the Original Source Repository

When discovering a skill through a catalogue such as `skills.sh`, locate the repository name shown on the skill page and open the original repository directly.

Review the folder containing the skill before downloading it.

### Step 2: Download the Complete Skill Folder

Copy or download the entire skill directory, not only the main Markdown file.

A skill may contain:

- `SKILL.md`;
- templates;
- examples;
- reference documents;
- scripts;
- schemas;
- configuration files;
- other supporting resources.

Preserve the original folder structure so relative file references continue to work.

Only copy a single file when you have confirmed that the skill genuinely contains no supporting files.

### Step 3: Add the Skill to This Repository

Place the complete skill folder inside:

`skills/agent_skills/<skill-name>/`

Example:

```text
skills/
└── agent_skills/
    └── qa-test-planner/
        ├── SKILL.md
        └── supporting-files/
```

Use a clear lowercase folder name. Prefer hyphens between words.

Do not place all skill files directly inside `skills/agent_skills/`. Each skill should have its own folder.

### Step 4: Check the Skill Contents

Review the copied skill for:

- absolute local paths;
- personal usernames;
- real Jira ticket keys;
- real repository names;
- environment-specific URLs;
- credentials;
- tokens;
- shell commands;
- downloads;
- write operations;
- instructions that bypass approval.

Unsafe machine-specific or project-specific values should not be committed as reusable skill defaults.

Do not silently change the meaning of the original skill. Any necessary adaptation should be reviewed and documented.

### Step 5: Reference the Skill From a Workflow

A skill should be used only by workflows that genuinely require it.

Add the skill reference to the appropriate approved workflow according to the repository’s existing workflow format.

Do not make a newly added skill globally mandatory unless it is genuinely required by every workflow.

The presence of a skill under `skills/agent_skills/` does not automatically authorise the agent to use it.

---

## Example: QA Test Planner

The `qa-test-planner` skill was discovered through `skills.sh`.

The catalogue showed the original repository containing the skill. The skill folder was then downloaded directly from that repository and manually copied into:

`skills/agent_skills/qa-test-planner/`

The complete skill package should be preserved, including `SKILL.md` and any supporting files referenced by it.

An approved workflow may then declare the skill as required for QA test planning.

The agent must not assume that every workflow requires the skill merely because it exists in the repository.

---

## Validate the Skill After Adding It

From the repository root, confirm the main skill file exists:

```powershell
Test-Path .\skills\agent_skills\<skill-name>\SKILL.md
```

Expected result:

```text
True
```

List all files in the skill folder:

```powershell
Get-ChildItem .\skills\agent_skills\<skill-name> -Recurse
```

Search for possible secrets or machine-specific values:

```powershell
rg -n -i "password|token|secret|api[_-]?key|private[_-]?key|C:\\Users|/home/" `
  .\skills\agent_skills\<skill-name>
```

Review every match manually. A match is not always a secret, but it must be checked.

Also verify:

- every referenced relative file exists;
- referenced templates or schemas are present;
- links point to the expected source;
- no approval or safety instruction is bypassed;
- the selected workflow names the correct skill folder.

Run the repository verification script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Unblock-File .\MCP\scripts\verify.ps1
& .\MCP\scripts\verify.ps1
```

Do not assume a skill works merely because its folder exists. Test it in a safe, non-production workflow before relying on it.

---

## Updating an Existing Skill

Before updating a skill:

1. Review changes in the original source repository.
2. Compare the new version with the currently installed version.
3. Check whether the local copy contains approved adaptations.
4. Preserve intentional local changes where required.
5. Review new scripts, links, commands, and dependencies.
6. Recheck licence and security requirements.
7. Run repository tests again.

When traceability is required, record:

- source repository;
- skill version;
- tag or commit hash;
- date added or updated;
- reviewer.

Do not overwrite a reviewed skill without examining upstream changes.

---

## Removing a Skill

Before removing a skill:

1. Search the repository for references to its folder name.
2. Check all active workflows.
3. Remove or replace workflow references.
4. Run architecture and verification tests.
5. Confirm no approved workflow still requires it.

Example search:

```powershell
rg -n "qa-test-planner" .
```

A missing mandatory skill must block workflow preflight. The agent must not invent or improvise replacement behaviour.

---

## Important Rules

- Review every skill before adding it.
- Prefer the original source repository over third-party copies.
- Copy the complete skill folder.
- Preserve supporting files and relative paths.
- Keep each skill in its own folder.
- Never store secrets inside a skill.
- Do not allow a skill to bypass repository approvals.
- Repository instructions and approved workflows take priority.
- Do not make a skill globally mandatory without a valid reason.
- Validate the skill before production use.
- Record the source and version when traceability is required.
