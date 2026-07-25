"""Initialize the stable local workspace for one Jira-scoped QA run.

The initializer creates source and generated-artifact directories, starter
documents, and a shared root log without replacing existing evidence. It owns
filesystem setup only; Jira retrieval and QA decisions belong to workflows.
"""

# region Imports and module setup
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TICKET_RUNS_ROOT = REPOSITORY_ROOT / "ticket_runs"
LOGS_ROOT = REPOSITORY_ROOT / "logs"
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
# endregion Imports and module setup


# region Function: Sanitize ticket key
def sanitize_ticket_key(ticket_key: str) -> str:
    """Return a deterministic, Windows-safe directory ID for a Jira key.

    Unsafe characters are replaced and changed values receive a short digest so
    distinct original keys do not silently collapse into the same run folder.
    """

    original = ticket_key.strip()
    normalized = original.upper()
    # Keep familiar ticket punctuation while removing separators and characters
    # that could escape or destabilize the ticket workspace.
    sanitized = re.sub(r"[^A-Z0-9._-]+", "_", normalized).strip("._-")
    if not sanitized:
        raise ValueError("The Jira ticket key must contain letters or numbers.")
    changed = sanitized != normalized or len(sanitized) > 100
    if changed:
        # A digest preserves deterministic uniqueness after replacement or
        # truncation without exposing additional ticket content.
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
        sanitized = sanitized[:90].rstrip("._-")
        sanitized = f"{sanitized}-{digest}"
    if sanitized.split(".", 1)[0] in _WINDOWS_RESERVED_NAMES:
        sanitized = f"RUN-{sanitized[:95]}"
    return sanitized
# endregion Function: Sanitize ticket key


# region Function: Safe run folder
def _safe_run_folder(ticket_runs_root: Path, ticket_id: str) -> Path:
    """Resolve a run path and reject links outside the ticket-runs root."""

    # Resolve before creating anything so a crafted identifier or linked path
    # cannot redirect ticket artifacts outside the configured root.
    root = ticket_runs_root.resolve()
    run_folder = root / ticket_id
    resolved_run_folder = run_folder.resolve(strict=False)
    if not resolved_run_folder.is_relative_to(root):
        raise ValueError("The run folder must remain inside the configured artifact root.")
    return run_folder
# endregion Function: Safe run folder


# region Function: Initial files
def _initial_files(ticket_id: str) -> dict[Path, str]:
    """Return relative starter paths and neutral content for a new run.

    These are placeholders for later workflow stages, not ticket conclusions.
    Callers create each path exclusively so repeat initialization is idempotent.
    """

    # The normalized result skeleton lets execution and reporting code share a
    # stable schema before any approved database check has run.
    empty_result = {
        "schema_version": "1.0",
        "ticket_id": ticket_id,
        "summary": {
            "status": "not_started",
        },
        "query_results": [],
        "errors": [],
    }

    return {
        Path("generated/ticket_context.md"): (
            f"# Ticket Context: {ticket_id}\n\n"
            "## Jira Ticket Key\n\n"
            f"`{ticket_id}`\n\n"
            "## Retrieved Context\n\n"
            "_To be populated by the agent through Atlassian MCP and supported files in "
            "the ticket's downloads folder._\n\n"
            "## Downloaded Source Files Reviewed\n\n"
            "_List relevant filenames or state that no local source files were required._\n\n"
            "## User Review\n\n"
            "Approval status: Pending\n"
        ),
        Path("generated/qa_plan.md"): (
            f"# QA Plan: {ticket_id}\n\n"
            "## Validation Objectives\n\n"
            "_Complete after the ticket context is approved._\n\n"
            "## Database Checks\n\n"
            "_List the required systems, profiles, checks, and expected outcomes._\n"
        ),
        Path("generated/generated_sql/generated_queries.sql"): (
            f"-- Generated validation queries for {ticket_id}\n"
            "-- Add queries only after the ticket context is approved.\n"
            "-- Give every statement a stable check ID and execute statements one at a time.\n"
            "-- Do not send these organizational comments to the database MCP.\n"
            "-- User approval is required before execution.\n"
        ),
        Path("generated/approvals/approval_log.md"): (
            f"# Approval Log: {ticket_id}\n\n"
            "| Timestamp (UTC) | Checkpoint | Decision | Notes |\n"
            "|---|---|---|---|\n"
        ),
        Path("generated/execution_results/execution_result.json"): json.dumps(empty_result, indent=2) + "\n",
    }
# endregion Function: Initial files


# region Function: Initialize run
def initialize_run(
    ticket_key: str,
    ticket_runs_root: Path | None = None,
    logs_root: Path | None = None,
) -> tuple[Path, list[Path]]:
    """Create missing ticket directories, starter artifacts, and the root log.

    ``ticket_key`` determines the safe run ID; optional roots support isolated
    tests. The returned tuple contains the run folder and only paths created by
    this call. Existing artifacts and log history are never overwritten.
    """

    ticket_id = sanitize_ticket_key(ticket_key)
    created_at = datetime.now(timezone.utc).isoformat()
    run_folder = _safe_run_folder(ticket_runs_root or TICKET_RUNS_ROOT, ticket_id)
    resolved_logs_root = (logs_root or LOGS_ROOT).resolve()
    # Directory creation is repeatable, while individual artifacts below use
    # exclusive file creation to preserve prior workflow state.
    run_folder.mkdir(parents=True, exist_ok=True)
    (run_folder / "downloads").mkdir(exist_ok=True)
    (run_folder / "generated").mkdir(exist_ok=True)
    resolved_logs_root.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for relative_path, content in _initial_files(ticket_id).items():
        path = run_folder / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # ``x`` mode is the idempotency boundary: an existing approval,
            # context, plan, SQL file, or result must survive a resumed run.
            with path.open("x", encoding="utf-8", newline="\n") as file:
                file.write(content)
        except FileExistsError:
            continue
        created.append(path)

    # Logs are shared at repository level by contract and are initialized once
    # so subsequent workflow activity can append without losing history.
    log_path = resolved_logs_root / f"{ticket_id}.log"
    try:
        with log_path.open("x", encoding="utf-8", newline="\n") as file:
            file.write(f"{created_at} | Run folder initialized | Success\n")
    except FileExistsError:
        # Preserve existing run history when initialization is repeated.
        pass
    else:
        created.append(log_path)

    return run_folder, created
# endregion Function: Initialize run


# region Function: Main
def main() -> int:
    """Run the ticket-workspace initializer command-line interface."""
    parser = argparse.ArgumentParser(description="Initialize a ticket-scoped QA run folder.")
    parser.add_argument("ticket_key", help="Jira ticket key, for example ABC-123")
    args = parser.parse_args()

    try:
        run_folder, created = initialize_run(args.ticket_key)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Unable to initialize the ticket run: {exc}\n")

    print(f"Run folder: {run_folder}")
    if created:
        print("Created missing files:")
        for path in created:
            print(f"- {path.name}")
    else:
        print("All run files already exist; no existing files were changed.")
    return 0
# endregion Function: Main


# region Command-line entry point
if __name__ == "__main__":
    raise SystemExit(main())
# endregion Command-line entry point
