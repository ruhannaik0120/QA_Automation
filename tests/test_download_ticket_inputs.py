"""Verify secure ticket-input acquisition, archive handling, and rollback.

In-memory HTTP responses and temporary workspaces exercise real downloader
logic without live URLs. The suite covers credential boundaries, path safety,
ZIP limits, atomic manifests, transactional extraction, and CLI failures.
"""

# region Imports and module setup
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

from modules import download_ticket_inputs
# endregion Imports and module setup


# region Function: ZIP bytes
def _zip_bytes(entries: list[tuple[str | zipfile.ZipInfo, bytes]]) -> bytes:
    """Build deterministic in-memory ZIP content for Office and package tests."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return buffer.getvalue()
# endregion Function: ZIP bytes


# region Function: Office bytes
def _office_bytes(document_type: str) -> bytes:
    """Build the minimum valid DOCX or XLSX package required by the validator."""

    member = "word/document.xml" if document_type == "docx" else "xl/workbook.xml"
    return _zip_bytes(
        [
            ("[Content_Types].xml", b"<Types/>"),
            (member, b"<document/>"),
        ]
    )
# endregion Function: Office bytes


# region Function: Text digest
def _text_digest(value: str) -> str:
    """Return a non-reversible comparison value for sensitive test headers."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
# endregion Function: Text digest


# region Function: Assert secret absent
def _assert_secret_absent(test_case: unittest.TestCase, secret: str, text: str) -> None:
    """Fail without echoing a sensitive value or inspected output."""

    if secret in text:
        test_case.fail("Sensitive test material appeared in observable output.")
# endregion Function: Assert secret absent


# region Function: Assert request header absent
def _assert_request_header_absent(
    test_case: unittest.TestCase,
    request: Request,
    header_name: str,
) -> None:
    """Fail without echoing a sensitive redirected header value."""

    if request.get_header(header_name) is not None:
        test_case.fail(f"Sensitive redirect header was retained: {header_name}")
# endregion Function: Assert request header absent


# region Class: Memory response
class _MemoryResponse:
    """Provide the urllib response surface without performing network access."""

    # region Function: Init
    def __init__(
        self,
        body: bytes,
        final_url: str,
        headers: dict[str, str] | None = None,
        status: int = 200,
    ):
        """Initialize one fresh in-memory response."""

        self._stream = io.BytesIO(body)
        self._final_url = final_url
        self.headers = Message()
        for name, value in (headers or {}).items():
            self.headers[name] = value
        self.status = status
    # endregion Function: Init

    # region Function: Enter
    def __enter__(self) -> "_MemoryResponse":
        """Enter the response context."""

        return self
    # endregion Function: Enter

    # region Function: Exit
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the response stream when its context ends."""

        self._stream.close()
    # endregion Function: Exit

    # region Function: Read
    def read(self, size: int = -1) -> bytes:
        """Read one response chunk."""

        return self._stream.read(size)
    # endregion Function: Read

    # region Function: Get URL
    def geturl(self) -> str:
        """Return the final URL after simulated redirects."""

        return self._final_url
    # endregion Function: Get URL

    # region Function: Get code
    def getcode(self) -> int:
        """Return the simulated HTTP status code."""

        return self.status
    # endregion Function: Get code
# endregion Class: Memory response


# region Class: Memory opener
class _MemoryOpener:
    """Record requests and return independent in-memory responses."""

    # region Function: Init
    def __init__(
        self,
        body: bytes,
        final_url: str,
        headers: dict[str, str] | None = None,
        status: int = 200,
    ):
        """Store response data and initialize request recording."""

        self.body = body
        self.final_url = final_url
        self.headers = headers or {}
        self.status = status
        self.requests: list[tuple[Request, float]] = []
    # endregion Function: Init

    # region Function: Open
    def open(self, request: Request, timeout: float) -> _MemoryResponse:
        """Record one request and return a fresh response."""

        self.requests.append((request, timeout))
        return _MemoryResponse(
            self.body,
            self.final_url,
            self.headers,
            self.status,
        )
    # endregion Function: Open
# endregion Class: Memory opener


# region Class: Download ticket input tests
class DownloadTicketInputTests(unittest.TestCase):
    """Verify downloader behavior without contacting external systems."""

    # region Function: Set up
    def setUp(self) -> None:
        """Create one initialized temporary ticket workspace."""

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.ticket_runs_root = self.root / "ticket_runs"
        self.run_folder = self.ticket_runs_root / "POC-123"
        self.downloads = self.run_folder / "downloads"
        self.generated = self.run_folder / "generated"
        self.downloads.mkdir(parents=True)
        self.generated.mkdir()
    # endregion Function: Set up

    # region Function: Tear down
    def tearDown(self) -> None:
        """Remove the temporary ticket workspace."""

        self.temporary_directory.cleanup()
    # endregion Function: Tear down

    # region Function: Direct download
    def _direct_download(
        self,
        *,
        body: bytes = b"%PDF-1.7\n",
        final_url: str = "http://127.0.0.1/input.pdf",
        expected_extension: str = ".pdf",
        auth_mode: str = "none",
        auth_profile: str | None = None,
        environment: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        output_name: str | None = None,
        max_bytes: int = download_ticket_inputs.DEFAULT_MAX_BYTES,
        overwrite: bool = False,
        archive_limits: download_ticket_inputs.ArchiveLimits | None = None,
    ) -> tuple[dict[str, object], _MemoryOpener]:
        """Download one in-memory response through the real direct-file workflow."""

        opener = _MemoryOpener(body, final_url, headers)
        result = download_ticket_inputs.download_direct_file(
            ticket_id="POC-123",
            url=final_url,
            expected_extension=expected_extension,
            auth_mode=auth_mode,
            auth_profile=auth_profile,
            allowed_hosts=("127.0.0.1",),
            output_name=output_name,
            max_bytes=max_bytes,
            ticket_runs_root=self.ticket_runs_root,
            environment=environment,
            opener=opener,
            overwrite=overwrite,
            archive_limits=archive_limits,
        )
        return result, opener
    # endregion Function: Direct download

    # region Function: Write package archive
    def _write_package_archive(
        self,
        entries: list[tuple[str | zipfile.ZipInfo, bytes]],
    ) -> Path:
        """Write one in-memory repository archive to the temporary workspace."""

        archive_path = self.root / "repository.zip"
        archive_path.write_bytes(_zip_bytes(entries))
        return archive_path
    # endregion Function: Write package archive

    # region Function: Extract package
    def _extract_package(
        self,
        entries: list[tuple[str | zipfile.ZipInfo, bytes]],
        *,
        package_path: str = "deployment/packages/qa",
        allowed_extensions: tuple[str, ...] = (".sql",),
        overwrite: bool = False,
        max_bytes: int = download_ticket_inputs.DEFAULT_MAX_BYTES,
        archive_limits: download_ticket_inputs.ArchiveLimits | None = None,
    ) -> list[Path]:
        """Extract one generated repository archive through the real package layer."""

        return download_ticket_inputs.extract_github_package(
            archive_path=self._write_package_archive(entries),
            package_path=package_path,
            extraction_root=self.downloads / "qa_scripts",
            allowed_extensions=allowed_extensions,
            overwrite=overwrite,
            max_bytes=max_bytes,
            archive_limits=archive_limits,
        )
    # endregion Function: Extract package

    # region Function: Test authentication profile prefix conversion
    def test_authentication_profile_prefix_conversion(self) -> None:
        """Convert profile punctuation to the expected uppercase prefix."""

        self.assertEqual(
            download_ticket_inputs.authentication_profile_prefix("document-read"),
            "DOCUMENT_READ",
        )
        self.assertEqual(
            download_ticket_inputs.authentication_profile_prefix("github-qa_read"),
            "GITHUB_QA_READ",
        )
    # endregion Function: Test authentication profile prefix conversion

    # region Function: Test unsafe ticket ID rejection
    def test_unsafe_ticket_id_and_traversal_rejection(self) -> None:
        """Reject traversal, separators, empty values, and reserved names."""

        for ticket_id in ("", "..", "../POC-123", "POC/123", r"POC\123", "CON"):
            with self.subTest(ticket_id=ticket_id):
                with self.assertRaises(download_ticket_inputs.WorkspaceError):
                    download_ticket_inputs.validate_ticket_id(ticket_id)
    # endregion Function: Test unsafe ticket ID rejection

    # region Function: Test unsafe direct filenames
    def test_unsafe_direct_filename_categories(self) -> None:
        """Reject every unsafe and Windows-incompatible filename category."""

        unsafe_names = {
            "empty": "",
            "dot": ".",
            "dot-dot": "..",
            "reserved": "CON.pdf",
            "reserved-extension": "lpt1.PDF",
            "alternate-data-stream": "report.pdf:private",
            "trailing-space": "report.pdf ",
            "trailing-dot": "report.pdf.",
            "forward-traversal": "../report.pdf",
            "backslash-traversal": r"..\report.pdf",
            "drive-qualified": r"C:\report.pdf",
            "absolute": "/report.pdf",
        }
        for category, filename in unsafe_names.items():
            with self.subTest(category=category):
                with self.assertRaises(download_ticket_inputs.SecurityValidationError):
                    download_ticket_inputs._validate_safe_filename(filename, ".pdf")
    # endregion Function: Test unsafe direct filenames

    # region Function: Test HTTPS and allowed host enforcement
    def test_https_and_allowed_host_enforcement(self) -> None:
        """Allow HTTPS and loopback HTTP while rejecting other HTTP or hosts."""

        parsed = download_ticket_inputs.validate_request_url(
            "https://files.example.com/file.pdf",
            ("files.example.com",),
        )
        self.assertEqual(parsed.hostname, "files.example.com")
        download_ticket_inputs.validate_request_url(
            "http://127.0.0.1/file.pdf",
            ("127.0.0.1",),
        )
        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            download_ticket_inputs.validate_request_url(
                "http://files.example.com/file.pdf",
                ("files.example.com",),
            )
        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            download_ticket_inputs.validate_request_url(
                "https://unrelated.example/file.pdf",
                ("files.example.com",),
            )
    # endregion Function: Test HTTPS and allowed host enforcement

    # region Function: Test embedded credential rejection
    def test_embedded_credential_rejection(self) -> None:
        """Reject usernames and passwords embedded in a request URL."""

        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            download_ticket_inputs.validate_request_url(
                "https://user:password@files.example.com/file.pdf",
                ("files.example.com",),
            )
    # endregion Function: Test embedded credential rejection

    # region Function: Test missing credential variables
    def test_missing_credential_environment_variables(self) -> None:
        """Name only missing profile variables when credentials are unavailable."""

        with self.assertRaises(download_ticket_inputs.AuthenticationProfileError) as context:
            download_ticket_inputs.authentication_headers(
                "basic",
                "document-read",
                {},
            )
        message = str(context.exception)
        self.assertIn("DOCUMENT_READ_USERNAME", message)
        self.assertIn("DOCUMENT_READ_PASSWORD", message)
    # endregion Function: Test missing credential variables

    # region Function: Test successful Basic authentication
    def test_successful_basic_authentication(self) -> None:
        """Send Basic credentials from environment variables without persisting them."""

        result, opener = self._direct_download(
            auth_mode="basic",
            auth_profile="document-read",
            environment={
                "DOCUMENT_READ_USERNAME": "qa-user",
                "DOCUMENT_READ_PASSWORD": "basic-secret",
            },
        )

        expected = base64.b64encode(b"qa-user:basic-secret").decode("ascii")
        actual_header = opener.requests[0][0].get_header("Authorization")
        self.assertIsNotNone(actual_header)
        self.assertEqual(
            _text_digest(actual_header or ""),
            _text_digest(f"Basic {expected}"),
        )
        manifest = (self.generated / "download_manifest.json").read_text(encoding="utf-8")
        _assert_secret_absent(self, "qa-user", manifest)
        _assert_secret_absent(self, "basic-secret", manifest)
        self.assertEqual(result["status"], "success")
    # endregion Function: Test successful Basic authentication

    # region Function: Test successful bearer authentication
    def test_successful_bearer_authentication(self) -> None:
        """Send a bearer token from its named environment profile."""

        result, opener = self._direct_download(
            auth_mode="bearer",
            auth_profile="document-read",
            environment={"DOCUMENT_READ_TOKEN": "bearer-secret"},
        )

        actual_header = opener.requests[0][0].get_header("Authorization")
        self.assertIsNotNone(actual_header)
        self.assertEqual(
            _text_digest(actual_header or ""),
            _text_digest("Bearer bearer-secret"),
        )
        self.assertEqual(result["status"], "success")
    # endregion Function: Test successful bearer authentication

    # region Function: Test secrets remain absent
    def test_secret_values_absent_from_output_errors_and_manifest(self) -> None:
        """Keep profile secrets out of output, exceptions, and failed manifests."""

        stdout = io.StringIO()
        stderr = io.StringIO()
        opener = _MemoryOpener(
            b"<html><title>Login error</title><form>Sign in</form></html>",
            "http://127.0.0.1/input.pdf?signature=signed-secret#fragment",
            {"Content-Type": "text/html"},
        )
        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(download_ticket_inputs.FileFormatError) as context:
                download_ticket_inputs.download_direct_file(
                    ticket_id="POC-123",
                    url="http://127.0.0.1/input.pdf?signature=signed-secret#fragment",
                    expected_extension=".pdf",
                    auth_mode="bearer",
                    auth_profile="document-read",
                    allowed_hosts=("127.0.0.1",),
                    ticket_runs_root=self.ticket_runs_root,
                    environment={"DOCUMENT_READ_TOKEN": "bearer-secret"},
                    opener=opener,
                )

        combined = stdout.getvalue() + stderr.getvalue() + str(context.exception)
        _assert_secret_absent(self, "bearer-secret", combined)
        _assert_secret_absent(self, "signed-secret", combined)
        self.assertFalse((self.generated / "download_manifest.json").exists())
    # endregion Function: Test secrets remain absent

    # region Function: Test valid DOCX acceptance
    def test_valid_docx_acceptance(self) -> None:
        """Accept a ZIP-based Word package with both required members."""

        result, _ = self._direct_download(
            body=_office_bytes("docx"),
            final_url="http://127.0.0.1/technical.docx",
            expected_extension=".docx",
        )

        self.assertEqual(result["detected_file_type"], "docx")
        self.assertTrue((self.downloads / "technical.docx").is_file())
    # endregion Function: Test valid DOCX acceptance

    # region Function: Test valid XLSX acceptance
    def test_valid_xlsx_acceptance(self) -> None:
        """Accept an Excel package with its content types and workbook members."""

        result, _ = self._direct_download(
            body=_office_bytes("xlsx"),
            final_url="http://127.0.0.1/evidence.xlsx",
            expected_extension=".xlsx",
        )

        self.assertEqual(result["detected_file_type"], "xlsx")
        self.assertTrue((self.downloads / "evidence.xlsx").is_file())
    # endregion Function: Test valid XLSX acceptance

    # region Function: Test invalid Office ZIP rejection
    def test_invalid_office_zip_rejection(self) -> None:
        """Reject a valid ZIP that lacks the required Office package members."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._direct_download(
                body=_zip_bytes([("unrelated.txt", b"not office")]),
                final_url="http://127.0.0.1/invalid.docx",
                expected_extension=".docx",
            )
    # endregion Function: Test invalid Office ZIP rejection

    # region Function: Test HTML login page rejection
    def test_http_200_html_login_page_rejection(self) -> None:
        """Reject a successful HTTP response that is actually a login page."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._direct_download(
                body=b"<html><title>Login</title><form>Sign in</form></html>",
                headers={"Content-Type": "text/html; charset=utf-8"},
            )
    # endregion Function: Test HTML login page rejection

    # region Function: Test empty response rejection
    def test_empty_response_rejection(self) -> None:
        """Reject an empty body before committing a destination file."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._direct_download(body=b"")
        self.assertFalse((self.downloads / "input.pdf").exists())
    # endregion Function: Test empty response rejection

    # region Function: Test maximum size enforcement
    def test_maximum_size_enforcement(self) -> None:
        """Stop streaming when the configured response limit is exceeded."""

        with self.assertRaises(download_ticket_inputs.DownloadSizeError):
            self._direct_download(body=b"%PDF-" + b"x" * 100, max_bytes=10)
    # endregion Function: Test maximum size enforcement

    # region Function: Test archive limit validation
    def test_archive_limits_must_be_positive(self) -> None:
        """Reject non-positive archive count, byte, and ratio limits."""

        invalid_values = (
            {"max_members": 0},
            {"max_total_uncompressed_bytes": 0},
            {"max_member_uncompressed_bytes": 0},
            {"max_compression_ratio": 0},
        )
        for values in invalid_values:
            with self.subTest(values=tuple(values)):
                with self.assertRaises(download_ticket_inputs.DownloadSizeError):
                    download_ticket_inputs.ArchiveLimits(**values)
    # endregion Function: Test archive limit validation

    # region Function: Test archive member count limit
    def test_archive_member_count_limit_precedes_decompression(self) -> None:
        """Reject excessive member counts before ZIP integrity decompression."""

        archive_path = self._write_package_archive(
            [
                ("root/deployment/packages/qa/one.sql", b"1"),
                ("root/deployment/packages/qa/two.sql", b"2"),
            ]
        )
        limits = download_ticket_inputs.ArchiveLimits(max_members=1)
        with patch.object(zipfile.ZipFile, "testzip") as testzip:
            with self.assertRaises(download_ticket_inputs.DownloadSizeError):
                download_ticket_inputs.validate_file_format(
                    archive_path,
                    ".zip",
                    archive_limits=limits,
                )
        testzip.assert_not_called()
    # endregion Function: Test archive member count limit

    # region Function: Test archive total size limit
    def test_archive_total_uncompressed_size_limit(self) -> None:
        """Reject archives whose aggregate expanded size exceeds its limit."""

        limits = download_ticket_inputs.ArchiveLimits(
            max_total_uncompressed_bytes=10,
            max_member_uncompressed_bytes=10,
        )
        with self.assertRaises(download_ticket_inputs.DownloadSizeError):
            self._extract_package(
                [
                    ("root/deployment/packages/qa/one.sql", b"123456"),
                    ("root/deployment/packages/qa/two.sql", b"123456"),
                ],
                archive_limits=limits,
            )
    # endregion Function: Test archive total size limit

    # region Function: Test archive member size limit
    def test_archive_individual_member_size_limit(self) -> None:
        """Reject one member whose expanded size exceeds its configured limit."""

        limits = download_ticket_inputs.ArchiveLimits(
            max_total_uncompressed_bytes=100,
            max_member_uncompressed_bytes=10,
        )
        with self.assertRaises(download_ticket_inputs.DownloadSizeError):
            self._extract_package(
                [("root/deployment/packages/qa/large.sql", b"x" * 11)],
                archive_limits=limits,
            )
    # endregion Function: Test archive member size limit

    # region Function: Test archive compression ratio limit
    def test_archive_extreme_compression_ratio_limit(self) -> None:
        """Reject highly compressed members before extracting their content."""

        limits = download_ticket_inputs.ArchiveLimits(
            max_total_uncompressed_bytes=20_000,
            max_member_uncompressed_bytes=20_000,
            max_compression_ratio=2.0,
        )
        with self.assertRaises(download_ticket_inputs.DownloadSizeError):
            self._extract_package(
                [("root/deployment/packages/qa/compressed.sql", b"A" * 10_000)],
                archive_limits=limits,
            )
    # endregion Function: Test archive compression ratio limit

    # region Function: Test partial cleanup
    def test_partial_file_cleanup_after_failure(self) -> None:
        """Delete partial files after signature validation fails."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._direct_download(body=b"not a pdf")
        self.assertEqual(list(self.downloads.glob("*.partial")), [])
    # endregion Function: Test partial cleanup

    # region Function: Test pre-existing partial preservation
    def test_pre_existing_partial_file_is_preserved(self) -> None:
        """Leave a partial path not owned by the current operation unchanged."""

        existing_partial = self.downloads / "input.pdf.partial"
        existing_partial.write_bytes(b"other-operation")

        self._direct_download()

        self.assertEqual(existing_partial.read_bytes(), b"other-operation")
        self.assertTrue((self.downloads / "input.pdf").is_file())
    # endregion Function: Test pre-existing partial preservation

    # region Function: Test concurrent destination collision
    def test_destination_collision_cannot_be_silently_overwritten(self) -> None:
        """Preserve a destination that appears during a no-overwrite commit."""

        destination = self.downloads / "input.pdf"

        # region Function: Create destination collision
        def create_collision(source: str | Path, target: str | Path) -> None:
            """Simulate another writer winning the destination race."""

            del source
            Path(target).write_bytes(b"concurrent-owner")
            raise FileExistsError
        # endregion Function: Create destination collision

        with patch.object(download_ticket_inputs.os, "link", side_effect=create_collision):
            with self.assertRaises(download_ticket_inputs.OverwriteProtectionError):
                self._direct_download()

        self.assertEqual(destination.read_bytes(), b"concurrent-owner")
        self.assertEqual(
            list(self.downloads.glob(".ticket-input-*.partial")),
            [],
        )
    # endregion Function: Test concurrent destination collision

    # region Function: Test overwrite protection
    def test_overwrite_protection_and_explicit_replacement(self) -> None:
        """Protect existing files unless the overwrite flag is supplied."""

        self._direct_download(body=b"%PDF-first")
        with self.assertRaises(download_ticket_inputs.OverwriteProtectionError):
            self._direct_download(body=b"%PDF-second")
        self.assertEqual((self.downloads / "input.pdf").read_bytes(), b"%PDF-first")

        self._direct_download(body=b"%PDF-second", overwrite=True)
        self.assertEqual((self.downloads / "input.pdf").read_bytes(), b"%PDF-second")
    # endregion Function: Test overwrite protection

    # region Function: Test manifest creation
    def test_successful_manifest_creation_preserves_entries(self) -> None:
        """Append a successful entry while preserving valid existing data."""

        manifest_path = self.generated / "download_manifest.json"
        manifest_path.write_text(
            json.dumps({"schema_version": "1.0", "downloads": [{"status": "existing"}]}),
            encoding="utf-8",
        )

        result, _ = self._direct_download()
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["downloads"][0]["status"], "existing")
        self.assertEqual(payload["downloads"][1], result)
        self.assertEqual(payload["downloads"][1]["source_type"], "direct_file")
    # endregion Function: Test manifest creation

    # region Function: Test manifest serialization failure
    def test_manifest_serialization_failure_preserves_previous_file(self) -> None:
        """Keep the previous manifest unchanged when JSON serialization fails."""

        manifest_path = self.generated / "download_manifest.json"
        previous = '{"schema_version":"1.0","downloads":[]}\n'
        manifest_path.write_text(previous, encoding="utf-8")

        with self.assertRaises(download_ticket_inputs.ManifestError):
            download_ticket_inputs.append_manifest_entry(
                manifest_path,
                {"unsupported": object()},
            )

        self.assertEqual(manifest_path.read_text(encoding="utf-8"), previous)
        self.assertEqual(list(self.generated.glob(".download-manifest-*.partial")), [])
    # endregion Function: Test manifest serialization failure

    # region Function: Test manifest replacement failure
    def test_manifest_replacement_failure_preserves_previous_file(self) -> None:
        """Keep the previous manifest and clean owned temporary files on replace failure."""

        manifest_path = self.generated / "download_manifest.json"
        previous = '{"schema_version":"1.0","downloads":[]}\n'
        manifest_path.write_text(previous, encoding="utf-8")

        with patch.object(
            download_ticket_inputs.os,
            "replace",
            side_effect=OSError("simulated replacement failure"),
        ):
            with self.assertRaises(download_ticket_inputs.ManifestError):
                download_ticket_inputs.append_manifest_entry(
                    manifest_path,
                    {"status": "success"},
                )

        self.assertEqual(manifest_path.read_text(encoding="utf-8"), previous)
        self.assertEqual(list(self.generated.glob(".download-manifest-*.partial")), [])
    # endregion Function: Test manifest replacement failure

    # region Function: Test invalid manifest preservation
    def test_invalid_existing_manifest_is_preserved_and_reported(self) -> None:
        """Reject invalid existing JSON without replacing or discarding its content."""

        manifest_path = self.generated / "download_manifest.json"
        invalid_content = "{invalid-json"
        manifest_path.write_text(invalid_content, encoding="utf-8")

        with self.assertRaises(download_ticket_inputs.ManifestError):
            download_ticket_inputs.append_manifest_entry(
                manifest_path,
                {"status": "success"},
            )

        self.assertEqual(
            manifest_path.read_text(encoding="utf-8"),
            invalid_content,
        )
        self.assertEqual(list(self.generated.glob(".download-manifest-*.partial")), [])
    # endregion Function: Test invalid manifest preservation

    # region Function: Test manifest URL sanitization
    def test_query_parameters_and_fragments_are_excluded_from_manifest(self) -> None:
        """Store only the scheme, host, port, and path of a source URL."""

        result, _ = self._direct_download(
            final_url="http://127.0.0.1/input.pdf?token=signed-value#private-fragment"
        )

        self.assertEqual(result["source_url"], "http://127.0.0.1/input.pdf")
        manifest = (self.generated / "download_manifest.json").read_text(encoding="utf-8")
        _assert_secret_absent(self, "signed-value", manifest)
        _assert_secret_absent(self, "private-fragment", manifest)
    # endregion Function: Test manifest URL sanitization

    # region Function: Test GitHub top-level handling
    def test_github_top_level_folder_handling(self) -> None:
        """Remove GitHub's generated archive root before exact package extraction."""

        archive_body = _zip_bytes(
            [("repository-random/deployment/packages/qa/check.sql", b"SELECT 1")]
        )
        opener = _MemoryOpener(
            archive_body,
            "https://codeload.github.com/owner/repository/legacy.zip/main",
            {"Content-Type": "application/zip"},
        )
        result = download_ticket_inputs.download_github_package(
            ticket_id="POC-123",
            repository="owner/repository",
            ref="main",
            package_path="deployment/packages/qa",
            auth_profile="github-qa-read",
            ticket_runs_root=self.ticket_runs_root,
            environment={"GITHUB_QA_READ_TOKEN": "github-secret"},
            opener=opener,
        )

        self.assertEqual(result["extracted_file_count"], 1)
        self.assertTrue((self.downloads / "qa_scripts" / "check.sql").is_file())
        self.assertTrue(Path(self.root, result["stored_archive_path"]).is_file())
        request = opener.requests[0][0]
        self.assertEqual(
            request.full_url,
            "https://api.github.com/repos/owner/repository/zipball/main",
        )
        actual_header = request.get_header("Authorization")
        self.assertIsNotNone(actual_header)
        self.assertEqual(
            _text_digest(actual_header or ""),
            _text_digest("Bearer github-secret"),
        )
    # endregion Function: Test GitHub top-level handling

    # region Function: Test exact package path matching
    def test_exact_package_path_matching(self) -> None:
        """Reject a similarly named package when the exact path is absent."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._extract_package(
                [("root/deployment/packages/qa-copy/check.sql", b"SELECT 1")]
            )
    # endregion Function: Test exact package path matching

    # region Function: Test permitted extension extraction
    def test_extracts_only_permitted_sql_files(self) -> None:
        """Ignore regular package files whose extensions were not allowed."""

        paths = self._extract_package(
            [
                ("root/deployment/packages/qa/check.sql", b"SELECT 1"),
                ("root/deployment/packages/qa/readme.txt", b"notes"),
            ]
        )

        self.assertEqual([path.name for path in paths], ["check.sql"])
        self.assertFalse((self.downloads / "qa_scripts" / "readme.txt").exists())
    # endregion Function: Test permitted extension extraction

    # region Function: Test safe subdirectory preservation
    def test_preserves_safe_package_subdirectories(self) -> None:
        """Preserve package-relative directories beneath qa_scripts."""

        paths = self._extract_package(
            [
                (
                    "root/deployment/packages/qa/post_validation/check.sql",
                    b"SELECT 1",
                )
            ]
        )

        expected = self.downloads / "qa_scripts" / "post_validation" / "check.sql"
        self.assertEqual(paths, [expected])
        self.assertTrue(expected.is_file())
    # endregion Function: Test safe subdirectory preservation

    # region Function: Test missing package failure
    def test_missing_package_failure(self) -> None:
        """Fail when the requested exact repository package does not exist."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._extract_package(
                [("root/other/location/check.sql", b"SELECT 1")]
            )
    # endregion Function: Test missing package failure

    # region Function: Test no permitted files failure
    def test_no_permitted_files_failure(self) -> None:
        """Fail when the selected package contains no allowed file type."""

        with self.assertRaises(download_ticket_inputs.FileFormatError):
            self._extract_package(
                [("root/deployment/packages/qa/readme.txt", b"notes")]
            )
    # endregion Function: Test no permitted files failure

    # region Function: Test archive traversal rejection
    def test_archive_traversal_rejection(self) -> None:
        """Reject traversal anywhere in the archive, including outside the package."""

        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            self._extract_package(
                [
                    ("root/deployment/packages/qa/check.sql", b"SELECT 1"),
                    ("root/../escape.sql", b"SELECT 2"),
                ]
            )
    # endregion Function: Test archive traversal rejection

    # region Function: Test backslash archive traversal rejection
    def test_backslash_archive_traversal_rejection(self) -> None:
        """Reject Windows-style traversal in every archive member."""

        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            self._extract_package(
                [
                    ("root/deployment/packages/qa/check.sql", b"SELECT 1"),
                    (r"root\..\escape.sql", b"SELECT 2"),
                ]
            )
    # endregion Function: Test backslash archive traversal rejection

    # region Function: Test Windows-incompatible archive components
    def test_windows_incompatible_archive_path_components(self) -> None:
        """Reject reserved, ambiguous, empty, drive, and ADS archive components."""

        unsafe_members = {
            "reserved": "root/unrelated/CON.sql",
            "reserved-extension": "root/unrelated/aux.notes",
            "alternate-data-stream": "root/unrelated/check.sql:private",
            "trailing-space": "root/unrelated/check.sql ",
            "trailing-dot": "root/unrelated/folder./check.sql",
            "empty": "root//check.sql",
            "dot": "root/./check.sql",
            "drive-qualified": "C:/check.sql",
        }
        for category, unsafe_member in unsafe_members.items():
            with self.subTest(category=category):
                with self.assertRaises(download_ticket_inputs.SecurityValidationError):
                    self._extract_package(
                        [
                            ("root/deployment/packages/qa/safe.sql", b"SELECT 1"),
                            (unsafe_member, b"SELECT 2"),
                        ]
                    )
    # endregion Function: Test Windows-incompatible archive components

    # region Function: Test absolute archive path rejection
    def test_absolute_archive_path_rejection(self) -> None:
        """Reject absolute member paths before extracting selected content."""

        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            self._extract_package(
                [
                    ("root/deployment/packages/qa/check.sql", b"SELECT 1"),
                    ("/absolute.sql", b"SELECT 2"),
                ]
            )
    # endregion Function: Test absolute archive path rejection

    # region Function: Test symbolic link rejection
    def test_symbolic_link_rejection(self) -> None:
        """Reject symbolic links even when a selected regular file is safe."""

        link = zipfile.ZipInfo("root/unrelated/link.sql")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            self._extract_package(
                [
                    ("root/deployment/packages/qa/check.sql", b"SELECT 1"),
                    (link, b"target.sql"),
                ]
            )
    # endregion Function: Test symbolic link rejection

    # region Function: Test extracted overwrite protection
    def test_existing_extracted_file_overwrite_protection(self) -> None:
        """Leave an existing extracted file unchanged without explicit overwrite."""

        extraction_root = self.downloads / "qa_scripts"
        extraction_root.mkdir()
        existing = extraction_root / "check.sql"
        existing.write_bytes(b"existing")

        with self.assertRaises(download_ticket_inputs.OverwriteProtectionError):
            self._extract_package(
                [("root/deployment/packages/qa/check.sql", b"replacement")]
            )
        self.assertEqual(existing.read_bytes(), b"existing")
    # endregion Function: Test extracted overwrite protection

    # region Function: Test new-file extraction rollback
    def test_transactional_extraction_rolls_back_new_files_and_directories(self) -> None:
        """Remove committed new files and owned directories after a later commit fails."""

        real_link = os.link
        link_count = 0

        # region Function: Fail second hard-link commit
        def fail_second_link(source: str | Path, target: str | Path) -> None:
            """Commit the first staged file and fail the second commit."""

            nonlocal link_count
            link_count += 1
            if link_count == 2:
                raise OSError("simulated commit failure")
            real_link(source, target)
        # endregion Function: Fail second hard-link commit

        with patch.object(download_ticket_inputs.os, "link", side_effect=fail_second_link):
            with self.assertRaises(download_ticket_inputs.DownloadRequestError):
                self._extract_package(
                    [
                        ("root/deployment/packages/qa/nested/one.sql", b"one"),
                        ("root/deployment/packages/qa/nested/two.sql", b"two"),
                    ]
                )

        self.assertFalse((self.downloads / "qa_scripts").exists())
        self.assertEqual(list(self.downloads.glob(".qa_scripts.staging-*")), [])
    # endregion Function: Test new-file extraction rollback

    # region Function: Test overwrite extraction rollback
    def test_transactional_extraction_restores_overwritten_files(self) -> None:
        """Restore every original file when a later overwrite commit fails."""

        extraction_root = self.downloads / "qa_scripts"
        extraction_root.mkdir()
        first = extraction_root / "one.sql"
        second = extraction_root / "two.sql"
        first.write_bytes(b"original-one")
        second.write_bytes(b"original-two")
        real_replace = os.replace
        payload_replace_count = 0

        # region Function: Fail second payload replacement
        def fail_second_payload_replace(source: str | Path, target: str | Path) -> None:
            """Replace the first payload and fail before replacing the second."""

            nonlocal payload_replace_count
            if "payload" in Path(source).parts:
                payload_replace_count += 1
                if payload_replace_count == 2:
                    raise OSError("simulated overwrite failure")
            real_replace(source, target)
        # endregion Function: Fail second payload replacement

        with patch.object(
            download_ticket_inputs.os,
            "replace",
            side_effect=fail_second_payload_replace,
        ):
            with self.assertRaises(OSError):
                self._extract_package(
                    [
                        ("root/deployment/packages/qa/one.sql", b"replacement-one"),
                        ("root/deployment/packages/qa/two.sql", b"replacement-two"),
                    ],
                    overwrite=True,
                )

        self.assertEqual(first.read_bytes(), b"original-one")
        self.assertEqual(second.read_bytes(), b"original-two")
        self.assertEqual(list(self.downloads.glob(".qa_scripts.staging-*")), [])
    # endregion Function: Test overwrite extraction rollback

    # region Function: Test CLI exit behavior
    def test_cli_success_and_failure_exit_behaviour(self) -> None:
        """Return zero for success and nonzero with structured stderr for failure."""

        success_output = io.StringIO()
        success_result = {
            "status": "success",
            "source_type": "direct_file",
            "ticket_id": "POC-123",
        }
        with patch.object(
            download_ticket_inputs,
            "download_direct_file",
            return_value=success_result,
        ), redirect_stdout(success_output):
            success_code = download_ticket_inputs.main(
                [
                    "file",
                    "--ticket-id",
                    "POC-123",
                    "--url",
                    "https://files.example.com/input.pdf",
                    "--expected-extension",
                    ".pdf",
                    "--auth-mode",
                    "none",
                    "--allowed-host",
                    "files.example.com",
                ]
            )

        failure_output = io.StringIO()
        with patch.object(
            download_ticket_inputs,
            "download_direct_file",
            side_effect=download_ticket_inputs.WorkspaceError("Workspace missing."),
        ), redirect_stderr(failure_output):
            failure_code = download_ticket_inputs.main(
                [
                    "file",
                    "--ticket-id",
                    "POC-123",
                    "--url",
                    "https://files.example.com/input.pdf",
                    "--expected-extension",
                    ".pdf",
                    "--auth-mode",
                    "none",
                    "--allowed-host",
                    "files.example.com",
                ]
            )

        self.assertEqual(success_code, 0)
        self.assertEqual(json.loads(success_output.getvalue())["status"], "success")
        self.assertEqual(failure_code, 1)
        self.assertEqual(json.loads(failure_output.getvalue())["status"], "error")
    # endregion Function: Test CLI exit behavior

    # region Function: Test real CLI nonzero failure
    def test_real_module_entry_point_returns_nonzero_without_network(self) -> None:
        """Run the real module command and report invalid limits as structured failure."""

        module_path = Path(download_ticket_inputs.__file__).resolve()
        with tempfile.TemporaryDirectory() as different_cwd:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(module_path),
                    "file",
                    "--ticket-id",
                    "NO-NETWORK-CLI-TEST",
                    "--url",
                    "https://files.example.com/input.pdf",
                    "--expected-extension",
                    ".pdf",
                    "--auth-mode",
                    "none",
                    "--allowed-host",
                    "files.example.com",
                    "--max-archive-members",
                    "0",
                ],
                cwd=different_cwd,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(json.loads(completed.stderr)["status"], "error")
    # endregion Function: Test real CLI nonzero failure

    # region Function: Test repository root from different CWD
    def test_repository_root_is_independent_of_current_working_directory(self) -> None:
        """Resolve the module repository root correctly from another process directory."""

        repository_root = Path(download_ticket_inputs.REPOSITORY_ROOT).resolve()
        probe = (
            "import sys;"
            "sys.path.insert(0, sys.argv[1]);"
            "from modules import download_ticket_inputs as module;"
            "print(module.REPOSITORY_ROOT.resolve())"
        )
        with tempfile.TemporaryDirectory() as different_cwd:
            completed = subprocess.run(
                [sys.executable, "-c", probe, str(repository_root)],
                cwd=different_cwd,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(Path(completed.stdout.strip()), repository_root)
        self.assertEqual(completed.stderr, "")
    # endregion Function: Test repository root from different CWD

    # region Function: Test structured secret-safe output
    def test_structured_and_secret_safe_json_output(self) -> None:
        """Emit parseable success JSON without credential or signed-URL values."""

        opener = _MemoryOpener(
            b"%PDF-1.7\n",
            "http://127.0.0.1/input.pdf?signed=private-query#private-fragment",
        )
        stdout = io.StringIO()
        with patch.object(
            download_ticket_inputs,
            "TICKET_RUNS_ROOT",
            self.ticket_runs_root,
        ), patch.object(
            download_ticket_inputs,
            "_build_validated_opener",
            return_value=opener,
        ), patch.dict(
            download_ticket_inputs.os.environ,
            {"DOCUMENT_READ_TOKEN": "private-token"},
            clear=False,
        ), redirect_stdout(stdout):
            exit_code = download_ticket_inputs.main(
                [
                    "file",
                    "--ticket-id",
                    "POC-123",
                    "--url",
                    "http://127.0.0.1/input.pdf?signed=private-query#private-fragment",
                    "--expected-extension",
                    ".pdf",
                    "--auth-mode",
                    "bearer",
                    "--auth-profile",
                    "document-read",
                    "--allowed-host",
                    "127.0.0.1",
                ]
            )

        output = stdout.getvalue()
        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "success")
        _assert_secret_absent(self, "private-token", output)
        _assert_secret_absent(self, "private-query", output)
        _assert_secret_absent(self, "private-fragment", output)
    # endregion Function: Test structured secret-safe output

    # region Function: Test redirect host validation
    def test_redirect_handler_rejects_unrelated_hosts(self) -> None:
        """Apply the allowlist to every redirect before urllib follows it."""

        handler = download_ticket_inputs._ValidatedRedirectHandler(
            ("files.example.com",),
            github_archive=False,
        )
        request = Request("https://files.example.com/input.pdf")
        with self.assertRaises(download_ticket_inputs.SecurityValidationError):
            handler.redirect_request(
                request,
                io.BytesIO(),
                302,
                "Found",
                Message(),
                "https://unrelated.example/login",
            )
    # endregion Function: Test redirect host validation

    # region Function: Test redirect origin header policy
    def test_redirect_preserves_sensitive_headers_only_for_same_origin(self) -> None:
        """Strip sensitive headers after scheme, hostname, or effective-port changes."""

        handler = download_ticket_inputs._ValidatedRedirectHandler(
            ("files.example.com", "mirror.example.com"),
            github_archive=False,
        )
        request = Request(
            "https://files.example.com/input.pdf",
            headers={
                "Authorization": "Bearer redirect-secret",
                "Proxy-Authorization": "Basic proxy-secret",
                "Cookie": "session=cookie-secret",
                "X-Api-Key": "api-key-secret",
            },
        )
        same_origin = handler.redirect_request(
            request,
            io.BytesIO(),
            302,
            "Found",
            Message(),
            "https://files.example.com:443/next.pdf",
        )
        self.assertIsNotNone(same_origin)
        preserved_header = (same_origin or request).get_header("Authorization")
        self.assertIsNotNone(preserved_header)
        self.assertEqual(
            _text_digest(preserved_header or ""),
            _text_digest("Bearer redirect-secret"),
        )

        changed_origins = (
            "https://files.example.com:8443/next.pdf",
            "https://mirror.example.com/next.pdf",
        )
        for destination_url in changed_origins:
            with self.subTest(destination_url=destination_url):
                changed_origin = handler.redirect_request(
                    request,
                    io.BytesIO(),
                    302,
                    "Found",
                    Message(),
                    destination_url,
                )
                self.assertIsNotNone(changed_origin)
                for header_name in (
                    "Authorization",
                    "Proxy-Authorization",
                    "Cookie",
                    "X-Api-Key",
                ):
                    _assert_request_header_absent(
                        self,
                        changed_origin or request,
                        header_name,
                    )

        loopback_handler = download_ticket_inputs._ValidatedRedirectHandler(
            ("127.0.0.1",),
            github_archive=False,
        )
        scheme_changed = loopback_handler.redirect_request(
            Request(
                "http://127.0.0.1/input.pdf",
                headers={"Authorization": "Bearer loopback-secret"},
            ),
            io.BytesIO(),
            302,
            "Found",
            Message(),
            "https://127.0.0.1/input.pdf",
        )
        self.assertIsNotNone(scheme_changed)
        _assert_request_header_absent(
            self,
            scheme_changed or request,
            "Authorization",
        )
    # endregion Function: Test redirect origin header policy

    # region Function: Test GitHub redirected token stripping
    def test_github_redirect_never_forwards_api_token_to_archive_host(self) -> None:
        """Remove the API token when GitHub redirects to an archive delivery host."""

        handler = download_ticket_inputs._ValidatedRedirectHandler(
            ("api.github.com",),
            github_archive=True,
        )
        request = Request(
            "https://api.github.com/repos/owner/repository/zipball/main",
            headers={"Authorization": "Bearer github-redirect-secret"},
        )

        redirected = handler.redirect_request(
            request,
            io.BytesIO(),
            302,
            "Found",
            Message(),
            "https://codeload.github.com/owner/repository/legacy.zip/main",
        )

        self.assertIsNotNone(redirected)
        _assert_request_header_absent(
            self,
            redirected or request,
            "Authorization",
        )
    # endregion Function: Test GitHub redirected token stripping

    # region Function: Test GitHub initial archive-host token stripping
    def test_github_token_is_not_sent_to_an_initial_archive_host(self) -> None:
        """Restrict API authorization even when an internal caller starts elsewhere."""

        opener = _MemoryOpener(
            _zip_bytes([("root/file.sql", b"SELECT 1")]),
            "https://codeload.github.com/owner/repository/archive.zip",
            {"Content-Type": "application/zip"},
        )
        download_ticket_inputs._download_to_directory(
            url="https://codeload.github.com/owner/repository/archive.zip",
            destination_directory=self.downloads,
            expected_extension=".zip",
            allowed_hosts=("api.github.com",),
            headers={"Authorization": "Bearer github-initial-secret"},
            output_name="archive.zip",
            max_bytes=download_ticket_inputs.DEFAULT_MAX_BYTES,
            timeout_seconds=1.0,
            overwrite=False,
            github_archive=True,
            opener=opener,
        )

        _assert_request_header_absent(
            self,
            opener.requests[0][0],
            "Authorization",
        )
    # endregion Function: Test GitHub initial archive-host token stripping
# endregion Class: Download ticket input tests


# region Unittest entry point
if __name__ == "__main__":
    unittest.main()
# endregion Unittest entry point
