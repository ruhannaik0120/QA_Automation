# QA Automation Repository Instructions

Read `Basic_Instructions.md` completely before acting on a QA ticket and treat it as the authoritative shared instruction source.

Discover Jira, source, database, and reporting tools by capability rather than by client-specific tool names. Route work from authoritative Jira metadata to the exact eligible workflow under `skills/workflows/`.

Run the shared read-only preflight before initializing a ticket workspace. Reconstruct resumed work from repository configuration and ticket artifacts, never from chat memory alone.

During ticket execution, write only under `ticket_runs/<ticket-id>/`, `logs/<ticket-id>.log`, and `output/<ticket-id>/`. Follow the selected workflow in order and stop only at its declared human approval checkpoints or an explicit operational blocker.
