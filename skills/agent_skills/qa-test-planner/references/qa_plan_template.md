# QA Plan Output Template

Use this planning-only template when the invoking workflow requires a Markdown
QA plan. Replace placeholders only with approved, authoritative information.
Leave unresolved values marked `blocked`; never guess them.

## Run Information

- **Ticket ID:** `<authoritative-ticket-id>`
- **Selected workflow:** `<exact-workflow-path>`
- **Invoking checklist item:** `<checklist-item-id>`
- **Skill key:** `qa-test-planner`
- **Context approval reference:** `<approval-record-or-blocked>`
- **Plan status:** `draft | blocked | ready_for_workflow_review`

`ready_for_workflow_review` means the draft is complete enough for the next
workflow checkpoint. It does not mean approved or ready for execution.

## Authoritative Sources

| Source role | Artifact or reference | Facts used | Approval state |
|---|---|---|---|
| Jira business request | `<authorized-reference>` | `<facts>` | `<state>` |
| Technical specification | `<authorized-reference>` | `<facts>` | `<state>` |
| Developer evidence | `<authorized-reference-or-not-applicable>` | `<facts>` | `<state>` |
| QA package inventory | `<authorized-reference-or-not-applicable>` | `<facts>` | `<state>` |

Do not place credentials, secrets, signed URLs, or confidential source content
in this table. Record safe artifact names or approved references only.

## Scope

### In Scope

- `<approved-scope-item>`

### Out Of Scope

- `<approved-exclusion-and-source>`

## Minimum Coverage Matrix

Use only `applicable`, `not_applicable`, or `blocked`. Every row requires a
reason and authoritative source.

| Category | Status | Reason | Authoritative source | Planned check IDs |
|---|---|---|---|---|
| Database, schema, and object existence | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Column names, data types, lengths, precision, scale, and nullability | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Source and target row counts | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Null checks | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Duplicate and uniqueness checks | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Primary-key and referential-integrity checks | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Source-to-target mappings | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Transformations and business rules | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Aggregate and reconciliation checks | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Incremental-load behavior | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Idempotency and safe rerun behavior | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Audit columns, timestamps, and load identifiers | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Boundary and negative cases | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Performance checks required by authoritative context | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |
| Rollback and recovery behavior | `<status>` | `<reason>` | `<source>` | `<ids-or-none>` |

## Planned Checks

Repeat this section for each applicable or blocked check.

### `<check-id>`: `<check-title>`

- **Objective:** `<approved-requirement-or-risk>`
- **Category:** `<coverage-category>`
- **Applicability:** `applicable | blocked`
- **Reason:** `<authoritative-reason>`
- **Authoritative source:** `<safe-source-reference>`
- **Prerequisites:** `<conditions-for-later-stage>`
- **Required inputs:** `<non-secret-inputs>`
- **Planned actions:** `<ordered-validation-intent-not-executed>`
- **Expected outcome:** `<authoritative-expected-result-or-blocked>`
- **Evidence required:** `<evidence-for-later-stage>`
- **Tool or system:** `<workflow-permitted-tool-or-not-applicable>`
- **Approval dependency:** `<required-workflow-checkpoint>`
- **Failure path:** `<workflow-defined-response>`

## Dependencies And Risks

| Item | Type | Impact | Required resolution |
|---|---|---|---|
| `<item>` | `dependency | risk | contradiction` | `<impact>` | `<resolution>` |

## Blockers And Questions

| ID | Missing or conflicting information | Why it blocks planning | Authorized resolver |
|---|---|---|---|
| `<blocker-id>` | `<question>` | `<impact>` | `<role-not-invented-person>` |

## Execution And Approval Handoff

- No live system or database was contacted while preparing this plan.
- No SQL or downloaded script was generated or executed by this skill.
- The plan does not approve itself or authorize execution.
- Context and execution approval gates remain separate.
- Later stages must apply their own SQL guard, profile, connector, and evidence
  requirements when database checks are applicable.
- **Next workflow checkpoint:** `<exact-checkpoint-or-blocked>`
