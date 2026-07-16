# Agent-Ready Repo Auditor

A dependency-free Python CLI and library that audits **public GitHub evidence** for coding-agent operational readiness. It reads one immutable default-branch snapshot and emits deterministic JSON or Markdown with source links for every positive finding.

It never clones or executes repository code. It is not a vulnerability scanner, security assessment, compliance review, or proof that documentation is accurate.

## GitHub Action

Add a deterministic public-evidence check to a repository:

```yaml
name: Agent readiness

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: wrightops-ai/agent-ready-repo-auditor@v1
        with:
          fail-threshold: "65"
```

The action writes `agent-ready-audit.md`, adds the evidence report to the workflow summary, and exposes `score`, `band`, `report-path`, and immutable `revision` outputs. Its token is used only for bounded read requests to `api.github.com`; private repositories still fail closed.

Want to see the output before installing it? [Request one free automated audit](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=audit-request.yml). Requests and reports are public. The form's remediation-interest question is non-binding demand research; this repository does not accept payment or create a service contract.

## Setup

Prerequisite: Python 3.10 or newer. There are no third-party runtime dependencies.

```bash
cd agent-ready-repo-auditor
python3 -m agent_ready_repo_auditor owner/repository --format markdown
```

Write both common delivery formats:

```bash
python3 -m agent_ready_repo_auditor owner/repository --format json --output audit.json
python3 -m agent_ready_repo_auditor owner/repository --format markdown --output audit.md
```

Accepted inputs are exactly `owner/repository` or a canonical `https://github.com/owner/repository` URL. Private, missing, inaccessible, or GitHub-truncated repositories fail closed without a partial score.

## Evidence model

The 100-point evidence score covers:

| Public evidence | Points |
| --- | ---: |
| Root README with setup guidance | 20 |
| Recognized coding-agent instructions | 20 |
| Redacted environment example | 10 |
| GitHub Actions workflow | 15 |
| Issue and pull-request templates | 10 |
| Verification commands or automation | 15 |
| Explicit risky-action boundaries | 10 |

Missing evidence means only that the artifact was not evidenced in the public default-branch snapshot. The report includes the inspected revision SHA, evidence URLs, limitations, warnings, and prioritized next steps.

Recognized agent instruction files are root `AGENTS.md`, root `CLAUDE.md`, `.github/copilot-instructions.md`, and root `.cursorrules`. Risk-boundary credit requires explicit prohibition or approval language tied to risky actions; a generic mention is not enough.

## Library usage

```python
from agent_ready_repo_auditor import audit_repository, render_json

report = audit_repository("owner/repository")
print(render_json(report), end="")
```

Successful JSON uses schema `agent-ready-repo-audit.v1`. Expected failures have a stable error object on standard error:

```json
{
  "error": {
    "code": "repository_inaccessible",
    "message": "Repository is private, missing, or otherwise inaccessible through the public GitHub API.",
    "retryable": false
  },
  "ok": false
}
```

Unauthenticated GitHub API limits apply to the CLI. The GitHub Action uses the workflow token for bounded API reads. Rate-limit failures include reset evidence when GitHub supplies it and never emit a partial audit.

## Verification

All automated tests use a mocked HTTP transport and make no network calls:

```bash
python3 -m unittest discover -v
python3 -m py_compile agent_ready_repo_auditor/*.py tests/*.py
```

An optional live smoke test can be run against any public repository:

```bash
python3 -m agent_ready_repo_auditor wrightops-ai/website --format json
```

## Commercial delivery boundary

This repository is suitable as the deterministic evidence engine for a human-reviewed readiness audit. A responsible paid delivery should state the scanned revision, manually verify the generated findings, add repository-specific priorities, and preserve the report's limitations. Do not market it as a security audit or promise operational outcomes that were not measured.

## License

MIT
