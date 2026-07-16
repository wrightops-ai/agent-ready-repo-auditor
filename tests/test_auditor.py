from __future__ import annotations

import base64
import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

from agent_ready_repo_auditor import audit_repository, parse_repository_ref, render_json, render_markdown
from agent_ready_repo_auditor import action_runtime, issue_fulfillment
from agent_ready_repo_auditor.errors import (
    GitHubRateLimitError,
    InputValidationError,
    PrivateRepositoryError,
    RepositoryTreeTruncatedError,
)
from agent_ready_repo_auditor.github import GitHubClient


COMMIT_SHA = "1" * 40
TREE_SHA = "2" * 40


class FakeResponse:
    def __init__(self, url: str, payload: dict[str, object]) -> None:
        self._url = url
        self._raw = json.dumps(payload).encode()
        self.headers = Message()
        self.headers["Content-Length"] = str(len(self._raw))

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url

    def read(self, limit: int = -1) -> bytes:
        return self._raw if limit < 0 else self._raw[:limit]


class GitHubFixture:
    def __init__(
        self,
        files: dict[str, str],
        *,
        private: bool = False,
        truncated: bool = False,
    ) -> None:
        self.calls: list[str] = []
        self.responses: dict[str, dict[str, object]] = {}
        base = "https://api.github.com/repos/acme/demo"
        self.responses[base] = {
            "archived": False,
            "default_branch": "main",
            "full_name": "acme/demo",
            "html_url": "https://github.com/acme/demo",
            "private": private,
        }
        self.responses[f"{base}/commits/main"] = {
            "commit": {"tree": {"sha": TREE_SHA}},
            "sha": COMMIT_SHA,
        }
        entries: list[dict[str, object]] = []
        for index, (path, text) in enumerate(sorted(files.items()), start=3):
            sha = f"{index:040x}"
            blob_url = f"{base}/git/blobs/{sha}"
            entries.append({"path": path, "sha": sha, "type": "blob", "url": blob_url})
            raw = text.encode()
            encoded = base64.b64encode(raw).decode()
            wrapped = "\n".join(encoded[offset : offset + 20] for offset in range(0, len(encoded), 20))
            self.responses[blob_url] = {
                "content": wrapped,
                "encoding": "base64",
                "size": len(raw),
            }
        self.responses[f"{base}/git/trees/{TREE_SHA}?recursive=1"] = {
            "tree": entries,
            "truncated": truncated,
        }

    def __call__(self, request: object, *, timeout: float) -> FakeResponse:
        del timeout
        url = getattr(request, "full_url")
        self.calls.append(url)
        return FakeResponse(url, self.responses[url])


def full_fixture() -> GitHubFixture:
    return GitHubFixture(
        {
            ".env.example": "TOKEN=replace-me\n",
            ".github/ISSUE_TEMPLATE/feature ](request).md": "# Feature request\n",
            ".github/pull_request_template.md": "# Change\n",
            ".github/workflows/ci.yml": "name: Tests\nsteps:\n  - run: python -m unittest\n",
            "AGENTS.md": "# Instructions\nDo not deploy or publish without explicit approval.\n",
            "README.md": "# Demo\n## Setup\nRun `python -m demo` after installation.\n## Tests\nRun tests locally.\n",
            "pyproject.toml": "[tool.pytest.ini_options]\ntestpaths = ['tests']\n",
            "scripts/check_repo.py": "print('check')\n",
            "src/file with space.py": "print('ok')\n",
        }
    )


class InputTests(unittest.TestCase):
    def test_accepts_slug_and_canonical_https_url(self) -> None:
        self.assertEqual(parse_repository_ref("acme/demo.git").slug, "acme/demo")
        self.assertEqual(parse_repository_ref("https://github.com/acme/demo").slug, "acme/demo")

    def test_rejects_noncanonical_or_unsafe_inputs(self) -> None:
        invalid = [
            "http://github.com/acme/demo",
            "https://evil.example/acme/demo",
            "https://github.com/acme/demo/issues",
            "https://github.com/acme/demo?tab=readme",
            "acme/demo extra",
            "acme//demo",
            "-acme/demo",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(InputValidationError):
                parse_repository_ref(value)


class AuditTests(unittest.TestCase):
    def test_full_fixture_scores_all_evidence_and_renders_deterministically(self) -> None:
        fixture = full_fixture()
        report = audit_repository("acme/demo", client=GitHubClient(transport=fixture))
        payload = report.to_dict()

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["score"], {
            "band": "well_evidenced", "earned": 100, "maximum": 100, "percentage": 100
        })
        self.assertEqual(payload["repository"]["revision_sha"], COMMIT_SHA)
        self.assertEqual(payload["next_steps"], [])
        self.assertNotIn("scripts/check_repo.py", payload["inspection"]["files"])

        rendered_once = render_json(report)
        rendered_twice = render_json(report)
        self.assertEqual(rendered_once, rendered_twice)
        self.assertEqual(json.loads(rendered_once)["schema_version"], "agent-ready-repo-audit.v1")

        markdown = render_markdown(report)
        self.assertIn("Evidence score: **100/100 (100%)**", markdown)
        self.assertIn(f"/blob/{COMMIT_SHA}/AGENTS.md#L2", markdown)
        self.assertIn("ISSUE_TEMPLATE/feature%20%5D%28request%29.md", markdown)
        self.assertNotIn("[feature ](request).md]", markdown)
        self.assertIn("not a vulnerability or security assessment", markdown)

    def test_minimal_fixture_reports_missing_evidence_without_inventing_it(self) -> None:
        fixture = GitHubFixture({"README.md": "# Demo\nIt never proves credential safety.\n"})
        report = audit_repository("acme/demo", client=GitHubClient(transport=fixture)).to_dict()

        self.assertEqual(report["score"]["earned"], 8)
        self.assertEqual(report["score"]["band"], "limited_public_evidence")
        self.assertEqual(len(report["next_steps"]), 7)
        self.assertTrue(all(check["status"] != "met" for check in report["checks"]))

    def test_private_and_truncated_repositories_fail_closed(self) -> None:
        with self.assertRaises(PrivateRepositoryError):
            audit_repository(
                "acme/demo",
                client=GitHubClient(transport=GitHubFixture({}, private=True)),
            )
        with self.assertRaises(RepositoryTreeTruncatedError):
            audit_repository(
                "acme/demo",
                client=GitHubClient(transport=GitHubFixture({}, truncated=True)),
            )

    def test_content_fetches_are_bounded_for_many_workflows(self) -> None:
        files = {"README.md": "# Demo\n"}
        files.update(
            {f".github/workflows/{number}.yml": "name: check\n" for number in range(10)}
        )
        fixture = GitHubFixture(files)
        audit_repository("acme/demo", client=GitHubClient(transport=fixture))

        blob_calls = [url for url in fixture.calls if "/git/blobs/" in url]
        self.assertEqual(len(blob_calls), 6)

    def test_rate_limit_is_machine_readable_and_emits_no_report(self) -> None:
        headers = Message()
        headers["X-RateLimit-Remaining"] = "0"
        headers["X-RateLimit-Reset"] = "1999999999"

        def rate_limited(request: object, *, timeout: float) -> FakeResponse:
            del timeout
            url = getattr(request, "full_url")
            raise HTTPError(url, 403, "rate limited", headers, io.BytesIO(b'{"message":"limit"}'))

        with self.assertRaises(GitHubRateLimitError) as context:
            audit_repository("acme/demo", client=GitHubClient(transport=rate_limited))
        self.assertEqual(
            context.exception.to_dict(),
            {
                "code": "github_rate_limited",
                "details": {"reset_epoch": 1999999999},
                "message": "GitHub public API rate limit was reached; no partial audit was emitted.",
                "retryable": True,
            },
        )


class GitHubActionTests(unittest.TestCase):
    def test_action_writes_report_summary_and_outputs(self) -> None:
        report = audit_repository(
            "acme/demo",
            client=GitHubClient(transport=full_fixture()),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_file = root / "github-output.txt"
            summary_file = root / "summary.md"
            environment = {
                "AUDIT_FORMAT": "markdown",
                "AUDIT_GITHUB_TOKEN": "test-token",
                "AUDIT_OUTPUT_FILE": "reports/agent-ready.md",
                "AUDIT_REPOSITORY": "acme/demo",
                "AUDIT_THRESHOLD": "90",
                "GITHUB_OUTPUT": str(output_file),
                "GITHUB_STEP_SUMMARY": str(summary_file),
                "GITHUB_WORKSPACE": str(root),
            }
            with mock.patch.object(action_runtime, "audit_repository", return_value=report) as audit:
                result = action_runtime.run(environment)

            self.assertEqual(result, 0)
            self.assertEqual(audit.call_args.args[0], "acme/demo")
            self.assertEqual(audit.call_args.kwargs["client"].token, "test-token")
            self.assertTrue((root / "reports" / "agent-ready.md").exists())
            self.assertIn("Evidence score: **100/100", summary_file.read_text(encoding="utf-8"))
            self.assertEqual(
                output_file.read_text(encoding="utf-8").splitlines(),
                [
                    "score=100",
                    "band=well_evidenced",
                    "report-path=reports/agent-ready.md",
                    f"revision={COMMIT_SHA}",
                ],
            )

    def test_action_rejects_output_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = {
                "AUDIT_OUTPUT_FILE": "../escape.md",
                "AUDIT_REPOSITORY": "acme/demo",
                "GITHUB_WORKSPACE": directory,
            }
            with mock.patch.object(action_runtime, "audit_repository") as audit:
                result = action_runtime.run(environment)

            self.assertEqual(result, 2)
            audit.assert_not_called()

    def test_action_threshold_fails_after_preserving_report(self) -> None:
        report = audit_repository(
            "acme/demo",
            client=GitHubClient(transport=GitHubFixture({"README.md": "# Demo\n"})),
        )
        with tempfile.TemporaryDirectory() as directory:
            environment = {
                "AUDIT_OUTPUT_FILE": "audit.md",
                "AUDIT_REPOSITORY": "acme/demo",
                "AUDIT_THRESHOLD": "100",
                "GITHUB_WORKSPACE": directory,
            }
            with mock.patch.object(action_runtime, "audit_repository", return_value=report):
                result = action_runtime.run(environment)

            self.assertEqual(result, 1)
            self.assertTrue((Path(directory) / "audit.md").exists())


class IssueFulfillmentTests(unittest.TestCase):
    def test_extracts_repository_from_issue_form(self) -> None:
        body = (
            "### Public repository\n\n"
            "https://github.com/acme/demo\n\n"
            "### Coding-agent workflow\n\nCodex\n"
        )
        self.assertEqual(issue_fulfillment.extract_repository(body), "acme/demo")

    def test_comment_is_disclosed_and_preserves_report_limits(self) -> None:
        report = audit_repository(
            "acme/demo",
            client=GitHubClient(transport=full_fixture()),
        )
        comment = issue_fulfillment.build_comment(report)
        self.assertIn("automatically generated", comment)
        self.assertIn("not a vulnerability or security assessment", comment)
        self.assertIn("Evidence score: **100/100", comment)


if __name__ == "__main__":
    unittest.main()
