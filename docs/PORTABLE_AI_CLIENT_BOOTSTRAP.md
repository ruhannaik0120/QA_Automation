# Portable AI Client Bootstrap

1. Clone the repository and open its root in the supported AI development client.
2. Create the project Python environment and install `requirements-e2e.txt` plus `MCP/requirements.txt`.
3. Configure an authorized Atlassian OAuth connection with direct Jira issue retrieval.
4. Set `QA_POC_GITHUB_TOKEN` through the approved environment or secret manager; never put its value in repository files.
5. Register Jira, GitHub, and database MCP servers by capability using client-supported configuration.
6. Configure secret-backed database profiles whose safe metadata matches the route-selected targets in `ticket_run_config.json`.
7. Verify `.github/copilot-instructions.md` is active and resolves `Basic_Instructions.md` as authoritative.
8. Make the two configured Jira attachment files available through an authorized bootstrap or manual path, then validate their actual type, size, and SHA-256 before treating them as reviewed inputs.
9. Run a read-only smoke test for direct Jira retrieval, GitHub authentication, database-profile discovery, connection diagnostics, and report dependencies. Do not execute ticket SQL.
10. Start with: `Run the end-to-end QA workflow for KAN-7.`

This guide is client-portable. A company laptop is one supported runtime, not the permanent architecture target.
