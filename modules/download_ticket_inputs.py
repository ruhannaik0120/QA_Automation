"""Securely download declared external inputs into an initialized ticket run."""

# region Imports and module setup
from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
import math
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import SplitResult, quote, unquote, urlsplit, urlunsplit
from urllib.request import (
    HTTPRedirectHandler,
    OpenerDirector,
    Request,
    build_opener,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TICKET_RUNS_ROOT = REPOSITORY_ROOT / "ticket_runs"
DEFAULT_MAX_BYTES = 104_857_600
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_ARCHIVE_MEMBERS = 5_000
DEFAULT_MAX_ARCHIVE_TOTAL_BYTES = 104_857_600
DEFAULT_MAX_ARCHIVE_MEMBER_BYTES = 52_428_800
DEFAULT_MAX_COMPRESSION_RATIO = 100.0
DOWNLOAD_CHUNK_SIZE = 64 * 1024
SUPPORTED_DIRECT_EXTENSIONS = {".csv", ".docx", ".pdf", ".xlsx", ".zip"}
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
_GITHUB_ARCHIVE_HOSTS = {
    "api.github.com",
    "codeload.github.com",
    "github.com",
    "github-releases.githubusercontent.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
_GITHUB_ARCHIVE_SUFFIXES = (".githubusercontent.com",)
_SENSITIVE_REDIRECT_HEADERS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "cookie2",
    "api-key",
    "x-api-key",
    "x-auth-token",
    "x-access-token",
}
# endregion Imports and module setup


# region Class: Ticket input error
class TicketInputError(Exception):
    """Base class for safe, user-facing ticket-input failures."""
# endregion Class: Ticket input error


# region Class: Workspace error
class WorkspaceError(TicketInputError):
    """Report a missing or unsafe ticket workspace."""
# endregion Class: Workspace error


# region Class: Security validation error
class SecurityValidationError(TicketInputError):
    """Report a rejected URL, filename, archive member, or path."""
# endregion Class: Security validation error


# region Class: Authentication profile error
class AuthenticationProfileError(TicketInputError):
    """Report missing or invalid environment-backed credentials."""
# endregion Class: Authentication profile error


# region Class: Download request error
class DownloadRequestError(TicketInputError):
    """Report a secret-safe HTTP or streaming failure."""
# endregion Class: Download request error


# region Class: Download size error
class DownloadSizeError(TicketInputError):
    """Report a response or extraction that exceeds its byte limit."""
# endregion Class: Download size error


# region Class: File format error
class FileFormatError(TicketInputError):
    """Report content that does not match its declared file type."""
# endregion Class: File format error


# region Class: Overwrite protection error
class OverwriteProtectionError(TicketInputError):
    """Report an existing destination protected from replacement."""
# endregion Class: Overwrite protection error


# region Class: Manifest error
class ManifestError(TicketInputError):
    """Report an invalid or unwritable download manifest."""
# endregion Class: Manifest error


# region Class: Archive limits
@dataclass(frozen=True, slots=True)
class ArchiveLimits:
    """Define validated metadata limits applied before ZIP decompression."""

    max_members: int = DEFAULT_MAX_ARCHIVE_MEMBERS
    max_total_uncompressed_bytes: int = DEFAULT_MAX_ARCHIVE_TOTAL_BYTES
    max_member_uncompressed_bytes: int = DEFAULT_MAX_ARCHIVE_MEMBER_BYTES
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO

    # region Function: Post init
    def __post_init__(self) -> None:
        """Reject non-positive, non-numeric, or non-finite archive limits."""

        integer_limits = (
            self.max_members,
            self.max_total_uncompressed_bytes,
            self.max_member_uncompressed_bytes,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in integer_limits
        ):
            raise DownloadSizeError("Archive count and byte limits must be positive integers.")
        if (
            isinstance(self.max_compression_ratio, bool)
            or not isinstance(self.max_compression_ratio, (int, float))
            or not math.isfinite(float(self.max_compression_ratio))
            or self.max_compression_ratio <= 0
        ):
            raise DownloadSizeError("Maximum archive compression ratio must be positive and finite.")
    # endregion Function: Post init
# endregion Class: Archive limits


# region Class: Download artifact
@dataclass(frozen=True, slots=True)
class DownloadArtifact:
    """Describe one validated file committed to the ticket workspace."""

    path: Path
    size: int
    sha256: str
    content_type: str
    detected_type: str
    sanitized_source_url: str
# endregion Class: Download artifact


# region Function: UTC timestamp
def _utc_timestamp() -> str:
    """Return an ISO-8601 completion timestamp in UTC."""

    return datetime.now(timezone.utc).isoformat()
# endregion Function: UTC timestamp


# region Function: Authentication profile prefix
def authentication_profile_prefix(profile: str) -> str:
    """Convert a safe profile name into an environment-variable prefix."""

    normalized = profile.strip()
    if not normalized or not re.fullmatch(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*", normalized):
        raise AuthenticationProfileError(
            "Authentication profile names may contain only letters, numbers, dots, hyphens, and underscores."
        )
    return re.sub(r"[^A-Za-z0-9]", "_", normalized).upper()
# endregion Function: Authentication profile prefix


# region Function: Required environment values
def _required_environment_values(
    names: Sequence[str],
    environment: Mapping[str, str],
) -> list[str]:
    """Read required secret values while naming only missing variables."""

    missing = [name for name in names if not environment.get(name)]
    if missing:
        raise AuthenticationProfileError(
            f"Missing required credential environment variables: {', '.join(missing)}"
        )
    return [environment[name] for name in names]
# endregion Function: Required environment values


# region Function: Authentication headers
def authentication_headers(
    auth_mode: str,
    auth_profile: str | None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build an authorization header from a named environment profile."""

    normalized_mode = auth_mode.strip().lower()
    if normalized_mode not in {"none", "basic", "bearer"}:
        raise AuthenticationProfileError("Authentication mode must be none, basic, or bearer.")
    if normalized_mode == "none":
        return {}
    if not auth_profile:
        raise AuthenticationProfileError(
            f"An authentication profile is required for {normalized_mode} authentication."
        )

    prefix = authentication_profile_prefix(auth_profile)
    values = environment if environment is not None else os.environ
    if normalized_mode == "basic":
        username_name = f"{prefix}_USERNAME"
        password_name = f"{prefix}_PASSWORD"
        username, password = _required_environment_values(
            (username_name, password_name),
            values,
        )
        encoded = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    token_name = f"{prefix}_TOKEN"
    token = _required_environment_values((token_name,), values)[0]
    return {"Authorization": f"Bearer {token}"}
# endregion Function: Authentication headers


# region Function: Normalize extension
def _normalize_extension(extension: str) -> str:
    """Return a lowercase extension with one safe leading dot."""

    normalized = extension.strip().lower()
    if not normalized.startswith("."):
        normalized = f".{normalized}"
    if not re.fullmatch(r"\.[a-z0-9]{1,16}", normalized):
        raise SecurityValidationError("File extensions must contain only a dot, letters, and numbers.")
    return normalized
# endregion Function: Normalize extension


# region Function: Validate ticket ID
def validate_ticket_id(ticket_id: str) -> str:
    """Accept an exact safe ticket directory name without rewriting it."""

    normalized = ticket_id.strip()
    if (
        not normalized
        or len(normalized) > 100
        or normalized in {".", ".."}
        or ".." in normalized
        or "/" in normalized
        or "\\" in normalized
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized)
    ):
        raise WorkspaceError("Ticket ID must be a safe existing directory name.")
    if normalized.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise WorkspaceError("Ticket ID uses a reserved directory name.")
    return normalized
# endregion Function: Validate ticket ID


# region Function: Safe child path
def _safe_child(root: Path, *parts: str) -> Path:
    """Resolve a child path and require it to remain inside its trusted root."""

    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*parts)
    resolved_candidate = candidate.resolve(strict=False)
    if not resolved_candidate.is_relative_to(resolved_root):
        raise SecurityValidationError("Destination path escapes its trusted ticket directory.")

    current = resolved_root
    for part in parts:
        current /= part
        if current.is_symlink():
            raise SecurityValidationError("Destination paths must not be symbolic links.")
    return candidate
# endregion Function: Safe child path


# region Function: Ticket workspace
def ticket_workspace(
    ticket_id: str,
    ticket_runs_root: Path | None = None,
) -> tuple[str, Path, Path]:
    """Return existing downloads and generated directories for one ticket."""

    safe_ticket_id = validate_ticket_id(ticket_id)
    root = (ticket_runs_root or TICKET_RUNS_ROOT).resolve()
    run_folder = _safe_child(root, safe_ticket_id)
    downloads = _safe_child(run_folder, "downloads")
    generated = _safe_child(run_folder, "generated")
    missing = [
        str(path.name)
        for path in (downloads, generated)
        if not path.is_dir() or path.is_symlink()
    ]
    if missing:
        raise WorkspaceError(
            "Ticket workspace is not initialized; missing required directories: "
            + ", ".join(missing)
        )
    return safe_ticket_id, downloads, generated
# endregion Function: Ticket workspace


# region Function: Normalize allowed hosts
def _normalize_allowed_hosts(hosts: Sequence[str]) -> set[str]:
    """Validate and normalize an explicit host allowlist."""

    normalized: set[str] = set()
    for host in hosts:
        candidate = host.strip().rstrip(".").lower()
        if (
            not candidate
            or "://" in candidate
            or "/" in candidate
            or "\\" in candidate
            or ":" in candidate
        ):
            raise SecurityValidationError("Allowed hosts must be hostnames without schemes, ports, or paths.")
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?", candidate):
                raise SecurityValidationError("Allowed host contains invalid characters.")
        normalized.add(candidate)
    if not normalized:
        raise SecurityValidationError("At least one allowed host is required.")
    return normalized
# endregion Function: Normalize allowed hosts


# region Function: Loopback host
def _is_loopback_host(host: str) -> bool:
    """Return whether a host is an explicit local-test loopback."""

    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False
# endregion Function: Loopback host


# region Function: Effective URL origin
def _effective_url_origin(url: str) -> tuple[str, str, int | None]:
    """Return a normalized scheme, hostname, and effective network port."""

    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").rstrip(".").lower()
    try:
        explicit_port = parsed.port
    except ValueError as exc:
        raise SecurityValidationError("Request URL contains an invalid port.") from exc
    default_port = 443 if scheme == "https" else 80 if scheme == "http" else None
    return scheme, host, explicit_port if explicit_port is not None else default_port
# endregion Function: Effective URL origin


# region Function: Sensitive redirect header
def _is_sensitive_redirect_header(name: str) -> bool:
    """Identify credentials and session material that must not cross origins."""

    normalized = name.lower()
    return (
        normalized in _SENSITIVE_REDIRECT_HEADERS
        or normalized.endswith("-api-key")
        or normalized.endswith("-auth-token")
        or normalized.endswith("-access-token")
    )
# endregion Function: Sensitive redirect header


# region Function: Strip sensitive redirect headers
def _strip_sensitive_redirect_headers(request: Request) -> None:
    """Remove credential-bearing headers from a redirected request."""

    header_names = {
        *request.headers,
        *request.unredirected_hdrs,
    }
    for header_name in header_names:
        if _is_sensitive_redirect_header(header_name):
            request.remove_header(header_name)
# endregion Function: Strip sensitive redirect headers


# region Function: GitHub archive host
def _is_github_archive_host(host: str) -> bool:
    """Return whether a redirect host belongs to GitHub archive delivery."""

    normalized = host.rstrip(".").lower()
    return normalized in _GITHUB_ARCHIVE_HOSTS or any(
        normalized.endswith(suffix) for suffix in _GITHUB_ARCHIVE_SUFFIXES
    )
# endregion Function: GitHub archive host


# region Function: Validate request URL
def validate_request_url(
    url: str,
    allowed_hosts: Sequence[str],
    *,
    github_archive: bool = False,
) -> SplitResult:
    """Validate URL credentials, scheme, and exact host policy."""

    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        raise SecurityValidationError("Request URLs must not contain embedded credentials.")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise SecurityValidationError("Request URL must contain a hostname.")

    normalized_hosts = _normalize_allowed_hosts(allowed_hosts)
    if github_archive:
        host_allowed = _is_github_archive_host(host)
    else:
        host_allowed = host in normalized_hosts
    if not host_allowed:
        raise SecurityValidationError(f"Request host is not allowed: {host}")

    scheme, _, port = _effective_url_origin(url)
    if port is not None and not 1 <= port <= 65535:
        raise SecurityValidationError("Request URL contains an invalid port.")
    if scheme == "https":
        return parsed
    if scheme == "http" and _is_loopback_host(host):
        return parsed
    raise SecurityValidationError("HTTPS is required except for explicit loopback test hosts.")
# endregion Function: Validate request URL


# region Function: Sanitized source URL
def sanitized_source_url(url: str) -> str:
    """Remove query parameters, fragments, and any user-information fields."""

    parsed = urlsplit(url)
    host = parsed.hostname or ""
    netloc = host
    if parsed.port is not None:
        netloc = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path, "", ""))
# endregion Function: Sanitized source URL


# region Class: Validated redirect handler
class _ValidatedRedirectHandler(HTTPRedirectHandler):
    """Revalidate every redirect before urllib follows it."""

    # region Function: Init
    def __init__(self, allowed_hosts: Sequence[str], *, github_archive: bool):
        """Store redirect policy without retaining authentication material."""

        super().__init__()
        self.allowed_hosts = tuple(allowed_hosts)
        self.github_archive = github_archive
    # endregion Function: Init

    # region Function: Redirect request
    def redirect_request(
        self,
        req: Request,
        fp: BinaryIO,
        code: int,
        msg: str,
        headers: Message,
        newurl: str,
    ) -> Request | None:
        """Reject unrelated redirect hosts before creating the next request."""

        destination = validate_request_url(
            newurl,
            self.allowed_hosts,
            github_archive=self.github_archive,
        )
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None

        origin_changed = _effective_url_origin(req.full_url) != _effective_url_origin(newurl)
        github_destination_is_api = (
            destination.hostname or ""
        ).rstrip(".").lower() == "api.github.com"
        if origin_changed or (self.github_archive and not github_destination_is_api):
            _strip_sensitive_redirect_headers(redirected)
        return redirected
    # endregion Function: Redirect request
# endregion Class: Validated redirect handler


# region Function: Build validated opener
def _build_validated_opener(
    allowed_hosts: Sequence[str],
    *,
    github_archive: bool,
) -> OpenerDirector:
    """Build an urllib opener whose redirects use the same host policy."""

    return build_opener(
        _ValidatedRedirectHandler(
            allowed_hosts,
            github_archive=github_archive,
        )
    )
# endregion Function: Build validated opener


# region Function: Validate path component
def _validate_path_component(component: str, *, description: str) -> str:
    """Reject unsafe or Windows-incompatible individual path components."""

    if (
        not component
        or component in {".", ".."}
        or component != component.strip()
        or component.endswith((" ", "."))
        or "/" in component
        or "\\" in component
        or ":" in component
        or "\x00" in component
        or len(component) > 240
    ):
        raise SecurityValidationError(f"{description} contains an unsafe path component.")
    device_stem = component.split(".", 1)[0].rstrip(" .").upper()
    if device_stem in _WINDOWS_RESERVED_NAMES:
        raise SecurityValidationError(f"{description} uses a reserved Windows device name.")
    return component
# endregion Function: Validate path component


# region Function: Validate safe filename
def _validate_safe_filename(filename: str, expected_extension: str) -> str:
    """Reject ambiguous, reserved, absolute, or extension-mismatched names."""

    normalized = filename
    if (
        not normalized
        or normalized in {".", ".."}
        or ".." in normalized
        or "/" in normalized
        or "\\" in normalized
        or "\x00" in normalized
        or Path(normalized).is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
    ):
        raise SecurityValidationError("No safe output filename could be established.")
    _validate_path_component(normalized, description="Output filename")
    if Path(normalized).suffix.lower() != expected_extension:
        raise FileFormatError(f"Output filename must end with {expected_extension}.")
    return normalized
# endregion Function: Validate safe filename


# region Function: Content disposition filename
def _content_disposition_filename(value: str) -> str:
    """Extract a standards-aware filename from Content-Disposition."""

    if not value:
        return ""
    message = Message()
    message["content-disposition"] = value
    return message.get_filename("") or ""
# endregion Function: Content disposition filename


# region Function: Select output filename
def _select_output_filename(
    output_name: str | None,
    content_disposition: str,
    source_url: str,
    expected_extension: str,
) -> str:
    """Select and validate the first available filename source."""

    if output_name is not None:
        return _validate_safe_filename(output_name, expected_extension)
    candidate = _content_disposition_filename(content_disposition)
    if not candidate:
        candidate = unquote(PurePosixPath(urlsplit(source_url).path).name)
    return _validate_safe_filename(candidate, expected_extension)
# endregion Function: Select output filename


# region Function: Detect HTML response
def _reject_html_response(path: Path, content_type: str) -> None:
    """Reject likely login, access-denied, and generic HTML error pages."""

    prefix = path.read_bytes()[:8192]
    decoded = prefix.decode("utf-8", errors="ignore").lower()
    normalized_content_type = content_type.lower()
    html_markers = ("<!doctype html", "<html", "<form", "<title")
    failure_markers = (
        "access denied",
        "authentication required",
        "error",
        "log in",
        "login",
        "sign in",
        "signin",
    )
    if "text/html" in normalized_content_type or (
        any(marker in decoded for marker in html_markers)
        and any(marker in decoded for marker in failure_markers)
    ):
        raise FileFormatError("Response appears to be an HTML login, access-denied, or error page.")
# endregion Function: Detect HTML response


# region Function: Enforce archive limits
def _enforce_archive_limits(
    archive: zipfile.ZipFile,
    limits: ArchiveLimits,
) -> list[zipfile.ZipInfo]:
    """Reject suspicious ZIP metadata before any member is decompressed."""

    members = archive.infolist()
    if len(members) > limits.max_members:
        raise DownloadSizeError(
            f"Archive exceeds the maximum of {limits.max_members} members."
        )

    total_uncompressed = 0
    for member in members:
        if member.file_size < 0 or member.compress_size < 0:
            raise FileFormatError("Archive contains invalid member size metadata.")
        if member.file_size > limits.max_member_uncompressed_bytes:
            raise DownloadSizeError(
                "Archive member exceeds the configured uncompressed byte limit."
            )
        total_uncompressed += member.file_size
        if total_uncompressed > limits.max_total_uncompressed_bytes:
            raise DownloadSizeError(
                "Archive exceeds the configured total uncompressed byte limit."
            )
        if member.file_size:
            if member.compress_size == 0:
                raise DownloadSizeError("Archive member has a suspicious compression ratio.")
            compression_ratio = member.file_size / member.compress_size
            if compression_ratio > limits.max_compression_ratio:
                raise DownloadSizeError(
                    "Archive member exceeds the configured compression-ratio limit."
                )
    return members
# endregion Function: Enforce archive limits


# region Function: Validate file format
def validate_file_format(
    path: Path,
    extension: str,
    *,
    archive_limits: ArchiveLimits | None = None,
) -> str:
    """Validate file signatures and required ZIP members without reading business content."""

    normalized_extension = _normalize_extension(extension)
    if normalized_extension not in SUPPORTED_DIRECT_EXTENSIONS:
        raise FileFormatError(f"Unsupported direct-file extension: {normalized_extension}")
    if not path.is_file() or path.stat().st_size <= 0:
        raise FileFormatError("Downloaded file is empty.")

    if normalized_extension == ".pdf":
        with path.open("rb") as file:
            if file.read(5) != b"%PDF-":
                raise FileFormatError("Downloaded content is not a valid PDF.")
    elif normalized_extension == ".csv":
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise FileFormatError("Downloaded CSV is not valid UTF-8 text.") from exc
        if not text or "\x00" in text:
            raise FileFormatError("Downloaded CSV is empty or contains binary data.")
    else:
        try:
            with zipfile.ZipFile(path) as archive:
                _enforce_archive_limits(
                    archive,
                    archive_limits or ArchiveLimits(),
                )
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise FileFormatError("Downloaded ZIP contains a corrupt member.")
                names = set(archive.namelist())
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            raise FileFormatError("Downloaded content is not a valid ZIP archive.") from exc

        required_members: set[str] = set()
        if normalized_extension == ".docx":
            required_members = {"[Content_Types].xml", "word/document.xml"}
        elif normalized_extension == ".xlsx":
            required_members = {"[Content_Types].xml", "xl/workbook.xml"}
        missing = required_members - names
        if missing:
            raise FileFormatError(
                f"Downloaded Office file is missing required package members: {', '.join(sorted(missing))}"
            )
    return normalized_extension.lstrip(".")
# endregion Function: Validate file format


# region Function: Commit partial file
def _commit_partial_file(partial_path: Path, destination: Path, *, overwrite: bool) -> None:
    """Atomically commit a validated partial file with explicit overwrite policy."""

    if overwrite:
        os.replace(partial_path, destination)
        return
    try:
        os.link(partial_path, destination)
    except FileExistsError as exc:
        raise OverwriteProtectionError(f"Destination already exists: {destination.name}") from exc
    except OSError as exc:
        raise DownloadRequestError(
            "Destination filesystem cannot perform a secure no-overwrite commit."
        ) from exc
    try:
        partial_path.unlink()
    except OSError as exc:
        try:
            destination_is_owned_link = (
                destination.exists()
                and partial_path.exists()
                and os.path.samefile(partial_path, destination)
            )
        except OSError:
            destination_is_owned_link = False
        if destination_is_owned_link:
            destination.unlink(missing_ok=True)
        raise DownloadRequestError("Unable to finalize a secure no-overwrite commit.") from exc
# endregion Function: Commit partial file


# region Function: Stream response
def _stream_response(
    response: BinaryIO,
    output: BinaryIO,
    *,
    max_bytes: int,
) -> tuple[int, str]:
    """Stream one response to disk while enforcing size and calculating SHA-256."""

    content_length = getattr(response, "headers", {}).get("Content-Length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError as exc:
            raise DownloadRequestError("Response contains an invalid Content-Length header.") from exc
        if declared_size > max_bytes:
            raise DownloadSizeError(f"Response exceeds the maximum of {max_bytes} bytes.")

    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise DownloadSizeError(f"Response exceeds the maximum of {max_bytes} bytes.")
        digest.update(chunk)
        output.write(chunk)
    if total == 0:
        raise FileFormatError("Downloaded response is empty.")
    return total, digest.hexdigest()
# endregion Function: Stream response


# region Function: Download to directory
def _download_to_directory(
    *,
    url: str,
    destination_directory: Path,
    expected_extension: str,
    allowed_hosts: Sequence[str],
    headers: Mapping[str, str],
    output_name: str | None,
    max_bytes: int,
    timeout_seconds: float,
    overwrite: bool,
    archive_limits: ArchiveLimits | None = None,
    github_archive: bool = False,
    opener: OpenerDirector | None = None,
) -> DownloadArtifact:
    """Download, validate, and atomically commit one file."""

    if max_bytes <= 0:
        raise DownloadSizeError("Maximum bytes must be greater than zero.")
    if timeout_seconds <= 0:
        raise DownloadRequestError("Timeout seconds must be greater than zero.")
    normalized_extension = _normalize_extension(expected_extension)
    parsed = validate_request_url(url, allowed_hosts, github_archive=github_archive)
    request_headers = {
        "Accept": "application/vnd.github+json" if github_archive else "*/*",
        "User-Agent": "qa-automation-ticket-input-downloader/1.0",
        **headers,
    }
    if github_archive and (parsed.hostname or "").rstrip(".").lower() != "api.github.com":
        request_headers = {
            name: value
            for name, value in request_headers.items()
            if not _is_sensitive_redirect_header(name)
        }
    request = Request(url, headers=request_headers, method="GET")
    active_opener = opener or _build_validated_opener(
        allowed_hosts,
        github_archive=github_archive,
    )
    host = parsed.hostname or "request host"
    partial_path: Path | None = None
    partial_descriptor: int | None = None

    try:
        with active_opener.open(request, timeout=timeout_seconds) as response:
            final_url = response.geturl()
            validate_request_url(
                final_url,
                allowed_hosts,
                github_archive=github_archive,
            )
            status = getattr(response, "status", response.getcode())
            if status is not None and int(status) >= 400:
                raise DownloadRequestError(f"Download request to {host} failed with HTTP status {status}.")

            content_type = response.headers.get("Content-Type", "")
            filename = _select_output_filename(
                output_name,
                response.headers.get("Content-Disposition", ""),
                final_url,
                normalized_extension,
            )
            destination = _safe_child(destination_directory, filename)
            if destination.exists() and not overwrite:
                raise OverwriteProtectionError(f"Destination already exists: {filename}")
            partial_descriptor, partial_name = tempfile.mkstemp(
                prefix=".ticket-input-",
                suffix=".partial",
                dir=destination_directory,
            )
            partial_path = Path(partial_name)
            with os.fdopen(partial_descriptor, "wb") as partial_file:
                partial_descriptor = None
                size, sha256 = _stream_response(
                    response,
                    partial_file,
                    max_bytes=max_bytes,
                )
            _reject_html_response(partial_path, content_type)
            detected_type = validate_file_format(
                partial_path,
                normalized_extension,
                archive_limits=archive_limits,
            )
            _commit_partial_file(partial_path, destination, overwrite=overwrite)
            partial_path = None
            return DownloadArtifact(
                path=destination,
                size=size,
                sha256=sha256,
                content_type=content_type,
                detected_type=detected_type,
                sanitized_source_url=sanitized_source_url(final_url),
            )
    except TicketInputError:
        raise
    except HTTPError as exc:
        raise DownloadRequestError(
            f"Download request to {host} failed with HTTP status {exc.code}."
        ) from exc
    except (TimeoutError, URLError) as exc:
        raise DownloadRequestError(f"Download request to {host} failed.") from exc
    except OSError as exc:
        raise DownloadRequestError(f"Unable to store the response from {host}.") from exc
    finally:
        if partial_descriptor is not None:
            os.close(partial_descriptor)
        if partial_path is not None:
            partial_path.unlink(missing_ok=True)
# endregion Function: Download to directory


# region Function: Project-relative path
def _project_relative(path: Path, ticket_runs_root: Path) -> str:
    """Return a stable path relative to the repository containing ticket_runs."""

    project_root = ticket_runs_root.resolve().parent
    resolved = path.resolve()
    if not resolved.is_relative_to(project_root):
        raise SecurityValidationError("Artifact path is outside the QA Automation repository.")
    return resolved.relative_to(project_root).as_posix()
# endregion Function: Project-relative path


# region Function: Load manifest
def _load_manifest(path: Path) -> dict[str, object]:
    """Load a valid manifest while preserving its existing entries and metadata."""

    if not path.exists():
        return {"schema_version": "1.0", "downloads": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError("Existing download manifest is not valid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("downloads"), list):
        raise ManifestError("Existing download manifest must contain a downloads list.")
    return payload
# endregion Function: Load manifest


# region Function: Append manifest entry
def append_manifest_entry(manifest_path: Path, entry: dict[str, object]) -> None:
    """Append one successful entry through an atomic secret-safe JSON write."""

    payload = _load_manifest(manifest_path)
    downloads = payload["downloads"]
    if not isinstance(downloads, list):
        raise ManifestError("Existing download manifest must contain a downloads list.")
    downloads.append(entry)

    try:
        serialized = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    except (TypeError, ValueError) as exc:
        raise ManifestError("Download manifest content is not JSON serializable.") from exc

    temporary_path: Path | None = None
    temporary_descriptor: int | None = None
    try:
        temporary_descriptor, temporary_name = tempfile.mkstemp(
            prefix=".download-manifest-",
            suffix=".partial",
            dir=manifest_path.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(
            temporary_descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as temporary_file:
            temporary_descriptor = None
            temporary_file.write(serialized)
        os.replace(temporary_path, manifest_path)
        temporary_path = None
    except OSError as exc:
        raise ManifestError("Unable to write the download manifest.") from exc
    finally:
        if temporary_descriptor is not None:
            os.close(temporary_descriptor)
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
# endregion Function: Append manifest entry


# region Function: Download direct file
def download_direct_file(
    *,
    ticket_id: str,
    url: str,
    expected_extension: str,
    auth_mode: str,
    auth_profile: str | None,
    allowed_hosts: Sequence[str],
    output_name: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    overwrite: bool = False,
    archive_limits: ArchiveLimits | None = None,
    ticket_runs_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
    opener: OpenerDirector | None = None,
) -> dict[str, object]:
    """Download one declared file and append its successful manifest entry."""

    active_root = (ticket_runs_root or TICKET_RUNS_ROOT).resolve()
    safe_ticket_id, downloads, generated = ticket_workspace(ticket_id, active_root)
    headers = authentication_headers(auth_mode, auth_profile, environment)
    artifact = _download_to_directory(
        url=url,
        destination_directory=downloads,
        expected_extension=expected_extension,
        allowed_hosts=allowed_hosts,
        headers=headers,
        output_name=output_name,
        max_bytes=max_bytes,
        timeout_seconds=timeout_seconds,
        overwrite=overwrite,
        archive_limits=archive_limits,
        opener=opener,
    )
    entry: dict[str, object] = {
        "status": "success",
        "source_type": "direct_file",
        "ticket_id": safe_ticket_id,
        "source_url": artifact.sanitized_source_url,
        "stored_path": _project_relative(artifact.path, active_root),
        "detected_file_type": artifact.detected_type,
        "content_type": artifact.content_type or None,
        "byte_size": artifact.size,
        "sha256": artifact.sha256,
        "completed_at": _utc_timestamp(),
    }
    append_manifest_entry(generated / "download_manifest.json", entry)
    return entry
# endregion Function: Download direct file


# region Function: Validate repository
def validate_repository(repository: str) -> tuple[str, str]:
    """Parse an exact owner/repository identifier without URL interpretation."""

    normalized = repository.strip()
    match = re.fullmatch(
        r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/([A-Za-z0-9_.-]{1,100})",
        normalized,
    )
    if not match or match.group(2) in {".", ".."} or ".." in match.group(2):
        raise SecurityValidationError("Repository must use exact owner/repository form.")
    return match.group(1), match.group(2)
# endregion Function: Validate repository


# region Function: Validate repository ref
def validate_repository_ref(ref: str) -> str:
    """Reject malformed or ambiguous Git ref values."""

    normalized = ref.strip()
    if (
        not normalized
        or len(normalized) > 255
        or normalized.startswith(("/", "."))
        or normalized.endswith(("/", "."))
        or ".." in normalized
        or "@{" in normalized
        or "\\" in normalized
        or any(ord(character) < 32 for character in normalized)
    ):
        raise SecurityValidationError("Repository ref is malformed.")
    return normalized
# endregion Function: Validate repository ref


# region Function: Validate package path
def validate_package_path(package_path: str) -> tuple[str, ...]:
    """Return exact safe POSIX path parts for a repository package."""

    normalized = package_path
    if (
        not normalized
        or normalized != normalized.strip()
        or normalized.startswith("/")
        or normalized.endswith("/")
        or "\\" in normalized
        or re.match(r"^[A-Za-z]:", normalized)
    ):
        raise SecurityValidationError("Package path must be an exact repository-relative path.")
    raw_parts = normalized.split("/")
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise SecurityValidationError("Package path must not contain traversal or empty segments.")
    for part in raw_parts:
        _validate_path_component(part, description="Package path")
    return tuple(raw_parts)
# endregion Function: Validate package path


# region Function: Normalize allowed extensions
def _normalize_allowed_extensions(extensions: Sequence[str] | None) -> set[str]:
    """Return the exact extension allowlist for package extraction."""

    supplied = extensions or (".sql",)
    return {_normalize_extension(extension) for extension in supplied}
# endregion Function: Normalize allowed extensions


# region Function: Archive filename
def _archive_filename(owner: str, repository: str, ref: str) -> str:
    """Build a deterministic filesystem-safe GitHub archive name."""

    safe_ref = re.sub(r"[^A-Za-z0-9._-]+", "-", ref).strip("._-")
    if not safe_ref:
        safe_ref = "ref"
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()[:10]
    base = f"{owner}-{repository}-{safe_ref}"[:180].rstrip("._-")
    return _validate_safe_filename(f"{base}-{digest}.zip", ".zip")
# endregion Function: Archive filename


# region Function: ZIP member parts
def _zip_member_parts(info: zipfile.ZipInfo) -> tuple[str, ...]:
    """Validate one archive member and return safe POSIX path components."""

    name = info.filename
    if (
        not name
        or "\x00" in name
        or "\\" in name
        or name.startswith("/")
        or re.match(r"^[A-Za-z]:", name)
    ):
        raise SecurityValidationError("Archive contains an absolute or malformed path.")

    raw_parts = name.split("/")
    if info.is_dir() and raw_parts[-1] == "":
        raw_parts = raw_parts[:-1]
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        raise SecurityValidationError("Archive contains path traversal or malformed segments.")
    for part in raw_parts:
        _validate_path_component(part, description="Archive member")

    mode = (info.external_attr >> 16) & 0xFFFF
    file_type = stat.S_IFMT(mode)
    if file_type == stat.S_IFLNK:
        raise SecurityValidationError("Archive contains a symbolic link.")
    if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
        raise SecurityValidationError("Archive contains a non-regular filesystem entry.")
    if info.flag_bits & 0x1:
        raise SecurityValidationError("Encrypted archive members are not supported.")
    return tuple(raw_parts)
# endregion Function: ZIP member parts


# region Function: Inspect package archive
def _inspect_package_archive(
    archive: zipfile.ZipFile,
    package_parts: tuple[str, ...],
    allowed_extensions: set[str],
) -> list[tuple[zipfile.ZipInfo, tuple[str, ...]]]:
    """Validate every member and select exact permitted package files."""

    inspected: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    normalized_names: set[tuple[str, ...]] = set()
    top_levels: set[str] = set()
    for info in archive.infolist():
        parts = _zip_member_parts(info)
        key = tuple(part.casefold() for part in parts)
        if key in normalized_names:
            raise SecurityValidationError("Archive contains duplicate or case-colliding paths.")
        normalized_names.add(key)
        top_levels.add(parts[0])
        inspected.append((info, parts))
    if len(top_levels) != 1:
        raise SecurityValidationError("GitHub archive must contain one generated top-level directory.")

    top_level = next(iter(top_levels))
    expected_prefix = (top_level, *package_parts)
    package_seen = False
    selected: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    for info, parts in inspected:
        if parts == expected_prefix or parts[: len(expected_prefix)] == expected_prefix:
            package_seen = True
        if info.is_dir() or parts[: len(expected_prefix)] != expected_prefix:
            continue
        relative_parts = parts[len(expected_prefix) :]
        if not relative_parts:
            continue
        if Path(relative_parts[-1]).suffix.lower() in allowed_extensions:
            selected.append((info, relative_parts))

    if not package_seen:
        raise FileFormatError("Exact requested package path does not exist in the repository archive.")
    if not selected:
        raise FileFormatError("Requested package contains no files with permitted extensions.")
    return selected
# endregion Function: Inspect package archive


# region Function: Create owned directory chain
def _create_owned_directory_chain(
    directory: Path,
    extraction_root: Path,
    owned_directories: list[Path],
) -> None:
    """Create missing extraction directories while recording exact ownership."""

    missing: list[Path] = []
    current = directory
    while True:
        if current.exists():
            if not current.is_dir() or current.is_symlink():
                raise SecurityValidationError(
                    "Extraction destination contains a non-directory or symbolic link."
                )
            break
        missing.append(current)
        if current == extraction_root:
            break
        if current == extraction_root.parent:
            raise SecurityValidationError("Extraction directory escapes its configured root.")
        current = current.parent

    for candidate in reversed(missing):
        try:
            candidate.mkdir()
        except FileExistsError:
            if not candidate.is_dir() or candidate.is_symlink():
                raise SecurityValidationError(
                    "Extraction destination changed to an unsafe path."
                )
        else:
            owned_directories.append(candidate)
# endregion Function: Create owned directory chain


# region Function: Remove owned directories
def _remove_owned_directories(owned_directories: Sequence[Path]) -> None:
    """Remove only operation-created extraction directories that remain empty."""

    for directory in reversed(owned_directories):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError:
            continue
# endregion Function: Remove owned directories


# region Function: Roll back extraction commits
def _rollback_extraction_commits(
    committed_destinations: Sequence[Path],
    backups: Mapping[Path, Path],
) -> None:
    """Restore overwritten files and remove new files owned by this operation."""

    rollback_error: OSError | None = None
    for destination in reversed(committed_destinations):
        backup = backups.get(destination)
        try:
            if backup is not None and backup.exists():
                os.replace(backup, destination)
            else:
                destination.unlink(missing_ok=True)
        except OSError as exc:
            rollback_error = rollback_error or exc
    if rollback_error is not None:
        raise DownloadRequestError("Unable to roll back a failed package extraction.") from rollback_error
# endregion Function: Roll back extraction commits


# region Function: Extract GitHub package
def extract_github_package(
    *,
    archive_path: Path,
    package_path: str,
    extraction_root: Path,
    allowed_extensions: Sequence[str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    overwrite: bool = False,
    archive_limits: ArchiveLimits | None = None,
) -> list[Path]:
    """Safely extract only permitted regular files from one exact package."""

    if max_bytes <= 0:
        raise DownloadSizeError("Maximum bytes must be greater than zero.")
    package_parts = validate_package_path(package_path)
    normalized_extensions = _normalize_allowed_extensions(allowed_extensions)
    active_archive_limits = archive_limits or ArchiveLimits()
    if not extraction_root.parent.is_dir() or extraction_root.parent.is_symlink():
        raise SecurityValidationError("Extraction parent must be an existing non-symbolic directory.")

    try:
        archive = zipfile.ZipFile(archive_path)
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise FileFormatError("GitHub repository archive is not a valid ZIP.") from exc

    staging_root: Path | None = None
    committed_destinations: list[Path] = []
    owned_directories: list[Path] = []
    backups: dict[Path, Path] = {}
    try:
        _enforce_archive_limits(archive, active_archive_limits)
        selected = _inspect_package_archive(
            archive,
            package_parts,
            normalized_extensions,
        )
        declared_total = sum(info.file_size for info, _ in selected)
        if declared_total > max_bytes:
            raise DownloadSizeError(f"Extracted package exceeds the maximum of {max_bytes} bytes.")

        destinations: list[tuple[zipfile.ZipInfo, tuple[str, ...], Path]] = []
        for info, relative_parts in selected:
            destination = _safe_child(extraction_root, *relative_parts)
            if destination.exists() and (destination.is_dir() or destination.is_symlink()):
                raise SecurityValidationError(
                    "Extracted destination must be a regular non-symbolic file."
                )
            if destination.exists() and not overwrite:
                raise OverwriteProtectionError(
                    f"Extracted destination already exists: {destination.name}"
                )
            destinations.append((info, relative_parts, destination))

        staging_root = Path(
            tempfile.mkdtemp(
                prefix=f".{extraction_root.name}.staging-",
                dir=extraction_root.parent,
            )
        )
        payload_root = staging_root / "payload"
        backup_root = staging_root / "backups"
        payload_root.mkdir()

        extracted_total = 0
        staged_files: list[tuple[Path, Path]] = []
        for info, relative_parts, destination in destinations:
            staged_path = _safe_child(payload_root, *relative_parts)
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            member_total = 0
            with archive.open(info, "r") as source, staged_path.open("xb") as output:
                while True:
                    chunk = source.read(DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    member_total += len(chunk)
                    extracted_total += len(chunk)
                    if (
                        member_total > active_archive_limits.max_member_uncompressed_bytes
                        or extracted_total > max_bytes
                        or extracted_total
                        > active_archive_limits.max_total_uncompressed_bytes
                    ):
                        raise DownloadSizeError(
                            "Extracted package exceeds its configured byte limits."
                        )
                    output.write(chunk)
            if member_total != info.file_size:
                raise FileFormatError("Extracted member size does not match ZIP metadata.")
            staged_files.append((staged_path, destination))

        if overwrite:
            backup_root.mkdir()
            for index, (_, destination) in enumerate(staged_files):
                if destination.exists():
                    backup = backup_root / f"{index}.backup"
                    shutil.copy2(destination, backup)
                    backups[destination] = backup

        for _, destination in staged_files:
            _create_owned_directory_chain(
                destination.parent,
                extraction_root,
                owned_directories,
            )

        for staged_path, destination in staged_files:
            _commit_partial_file(
                staged_path,
                destination,
                overwrite=overwrite,
            )
            committed_destinations.append(destination)
    except Exception:
        if committed_destinations:
            _rollback_extraction_commits(committed_destinations, backups)
        _remove_owned_directories(owned_directories)
        raise
    finally:
        archive.close()
        if staging_root is not None:
            shutil.rmtree(staging_root)
    return [destination for _, _, destination in destinations]
# endregion Function: Extract GitHub package


# region Function: Download GitHub package
def download_github_package(
    *,
    ticket_id: str,
    repository: str,
    ref: str,
    package_path: str,
    auth_profile: str,
    allowed_extensions: Sequence[str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    overwrite: bool = False,
    archive_limits: ArchiveLimits | None = None,
    ticket_runs_root: Path | None = None,
    environment: Mapping[str, str] | None = None,
    opener: OpenerDirector | None = None,
) -> dict[str, object]:
    """Download one authenticated GitHub archive and extract an exact package."""

    active_root = (ticket_runs_root or TICKET_RUNS_ROOT).resolve()
    safe_ticket_id, downloads, generated = ticket_workspace(ticket_id, active_root)
    owner, repository_name = validate_repository(repository)
    safe_ref = validate_repository_ref(ref)
    package_parts = validate_package_path(package_path)
    exact_package_path = "/".join(package_parts)
    normalized_extensions = sorted(_normalize_allowed_extensions(allowed_extensions))
    active_archive_limits = archive_limits or ArchiveLimits()
    headers = authentication_headers("bearer", auth_profile, environment)

    source_archives = _safe_child(downloads, "source_archives")
    extraction_root = _safe_child(downloads, "qa_scripts")
    source_archives.mkdir(parents=True, exist_ok=True)
    archive_name = _archive_filename(owner, repository_name, safe_ref)
    archive_url = (
        f"https://api.github.com/repos/{quote(owner, safe='')}/"
        f"{quote(repository_name, safe='')}/zipball/{quote(safe_ref, safe='')}"
    )
    artifact = _download_to_directory(
        url=archive_url,
        destination_directory=source_archives,
        expected_extension=".zip",
        allowed_hosts=("api.github.com",),
        headers=headers,
        output_name=archive_name,
        max_bytes=max_bytes,
        timeout_seconds=timeout_seconds,
        overwrite=overwrite,
        archive_limits=active_archive_limits,
        github_archive=True,
        opener=opener,
    )
    try:
        extracted_paths = extract_github_package(
            archive_path=artifact.path,
            package_path=exact_package_path,
            extraction_root=extraction_root,
            allowed_extensions=normalized_extensions,
            max_bytes=max_bytes,
            overwrite=overwrite,
            archive_limits=active_archive_limits,
        )
    except Exception:
        if not overwrite:
            artifact.path.unlink(missing_ok=True)
        raise

    entry: dict[str, object] = {
        "status": "success",
        "source_type": "github_package",
        "ticket_id": safe_ticket_id,
        "repository": f"{owner}/{repository_name}",
        "ref": safe_ref,
        "package_path": exact_package_path,
        "stored_archive_path": _project_relative(artifact.path, active_root),
        "archive_byte_size": artifact.size,
        "archive_sha256": artifact.sha256,
        "extracted_root_path": _project_relative(extraction_root, active_root),
        "extracted_file_paths": [
            _project_relative(path, active_root) for path in extracted_paths
        ],
        "extracted_file_count": len(extracted_paths),
        "completed_at": _utc_timestamp(),
    }
    append_manifest_entry(generated / "download_manifest.json", entry)
    return entry
# endregion Function: Download GitHub package


# region Function: Add archive limit arguments
def _add_archive_limit_arguments(parser: argparse.ArgumentParser) -> None:
    """Add configurable ZIP metadata safety limits to one subcommand."""

    parser.add_argument(
        "--max-archive-members",
        type=int,
        default=DEFAULT_MAX_ARCHIVE_MEMBERS,
    )
    parser.add_argument(
        "--max-archive-total-bytes",
        type=int,
        default=DEFAULT_MAX_ARCHIVE_TOTAL_BYTES,
    )
    parser.add_argument(
        "--max-archive-member-bytes",
        type=int,
        default=DEFAULT_MAX_ARCHIVE_MEMBER_BYTES,
    )
    parser.add_argument(
        "--max-compression-ratio",
        type=float,
        default=DEFAULT_MAX_COMPRESSION_RATIO,
    )
# endregion Function: Add archive limit arguments


# region Function: Archive limits from arguments
def _archive_limits_from_arguments(args: argparse.Namespace) -> ArchiveLimits:
    """Build validated archive limits from parsed command-line values."""

    return ArchiveLimits(
        max_members=args.max_archive_members,
        max_total_uncompressed_bytes=args.max_archive_total_bytes,
        max_member_uncompressed_bytes=args.max_archive_member_bytes,
        max_compression_ratio=args.max_compression_ratio,
    )
# endregion Function: Archive limits from arguments


# region Function: Build CLI parser
def build_parser() -> argparse.ArgumentParser:
    """Build the two-subcommand ticket-input downloader interface."""

    parser = argparse.ArgumentParser(
        description="Download declared external inputs into an initialized QA ticket run."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    file_parser = subparsers.add_parser("file", help="Download one direct file")
    file_parser.add_argument("--ticket-id", required=True)
    file_parser.add_argument("--url", required=True)
    file_parser.add_argument("--expected-extension", required=True)
    file_parser.add_argument("--auth-mode", required=True, choices=("none", "basic", "bearer"))
    file_parser.add_argument("--auth-profile")
    file_parser.add_argument("--allowed-host", action="append", required=True)
    file_parser.add_argument("--output-name")
    file_parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    file_parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    file_parser.add_argument("--overwrite", action="store_true")
    _add_archive_limit_arguments(file_parser)

    github_parser = subparsers.add_parser(
        "github-package",
        help="Download and extract one exact package from a GitHub repository archive",
    )
    github_parser.add_argument("--ticket-id", required=True)
    github_parser.add_argument("--repository", required=True)
    github_parser.add_argument("--ref", required=True)
    github_parser.add_argument("--package-path", required=True)
    github_parser.add_argument("--auth-profile", required=True)
    github_parser.add_argument("--allowed-extension", action="append")
    github_parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    github_parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    github_parser.add_argument("--overwrite", action="store_true")
    _add_archive_limit_arguments(github_parser)
    return parser
# endregion Function: Build CLI parser


# region Function: Main
def main(argv: Sequence[str] | None = None) -> int:
    """Run a download subcommand and emit one structured secret-safe result."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "file":
            result = download_direct_file(
                ticket_id=args.ticket_id,
                url=args.url,
                expected_extension=args.expected_extension,
                auth_mode=args.auth_mode,
                auth_profile=args.auth_profile,
                allowed_hosts=args.allowed_host,
                output_name=args.output_name,
                max_bytes=args.max_bytes,
                timeout_seconds=args.timeout_seconds,
                overwrite=args.overwrite,
                archive_limits=_archive_limits_from_arguments(args),
            )
        else:
            result = download_github_package(
                ticket_id=args.ticket_id,
                repository=args.repository,
                ref=args.ref,
                package_path=args.package_path,
                auth_profile=args.auth_profile,
                allowed_extensions=args.allowed_extension,
                max_bytes=args.max_bytes,
                timeout_seconds=args.timeout_seconds,
                overwrite=args.overwrite,
                archive_limits=_archive_limits_from_arguments(args),
            )
    except (TicketInputError, OSError) as exc:
        error = {
            "status": "error",
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
        print(json.dumps(error, ensure_ascii=True), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=True))
    return 0
# endregion Function: Main


# region Command-line entry point
if __name__ == "__main__":
    raise SystemExit(main())
# endregion Command-line entry point
