# Agent-Ready Repo Auditor

[![CI](https://github.com/wrightops-ai/agent-ready-repo-auditor/actions/workflows/ci.yml/badge.svg)](https://github.com/wrightops-ai/agent-ready-repo-auditor/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/wrightops-ai/agent-ready-repo-auditor)](https://github.com/wrightops-ai/agent-ready-repo-auditor/releases/latest)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#setup)
[![License: MIT](https://img.shields.io/badge/License-MIT-2F855A.svg)](LICENSE)

**Find the public setup, instruction, verification, and safety-boundary gaps that make coding agents unreliable.**

Agent-Ready Repo Auditor is a dependency-free Python CLI, library, and GitHub Action for repositories used with **Codex, Claude Code, GitHub Copilot coding agent, Cursor, or mixed-agent workflows**. It reads one immutable public default-branch snapshot and emits deterministic JSON or Markdown with source links for every positive finding.

[Explore the WrightOps offer site](https://zachwright.xyz/) · [Request a free automated audit](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=audit-request.yml) · [Request a $149 human-reviewed Fix Plan](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=fix-plan-request.yml) · [Request the $249 Founding Instructions PR](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=instructions-pr-request.yml) · [Inspect the real two-file sample PR](https://github.com/wrightops-ai/bounty-red-flag-card/pull/1) · [See the immutable audit report](docs/sample-report-v1.md) · [Install the GitHub Action](#github-action)

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

Want to see the output before installing it? [Request one free automated audit](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=audit-request.yml). Requests and reports are public. The form's remediation-interest question is non-binding demand research; opening an issue does not create a service contract.

Need exact next steps after the report? The [$149 Agent-Ready Repo Fix Plan](docs/agent-ready-fix-plan.md) adds exactly three human-reviewed fix cards to the public audit issue within one business day. [Submit the completed audit for automated preflight and scope confirmation](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=fix-plan-request.yml), then use the dedicated [PayPal goods/services checkout](https://www.paypal.com/ncp/payment/H9VVRGRGA3DCG) only after WrightOps confirms that the public request fits the fixed scope.

Need the two instruction files proposed as an actual contribution? The
[$249 Founding Agent-Ready Instructions PR](docs/agent-ready-instructions-pr.md)
adds or updates exactly root `AGENTS.md` plus one selected companion file—root
`CLAUDE.md` or `.github/copilot-instructions.md`—for one public repository,
then delivers one ready-to-merge pull request with one revision round. It uses
only committed public evidence and does not execute repository code. [Request
written scope confirmation](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=instructions-pr-request.yml);
the dedicated PayPal Goods & Services checkout is shared privately only after
scope confirmation. An eligible $149 Fix Plan for the same repository and
revision can be credited toward the $249 total. [Inspect the merged sample
PR](https://github.com/wrightops-ai/bounty-red-flag-card/pull/1) to see the
Copilot companion variant, exact two-file boundary, evidence notes, hosted
checks, and public review surface.

For a concrete example, read the [sample report for the immutable `v1` release](docs/sample-report-v1.md), generated from public evidence at revision `7a507bc0cb42f8c04fb18e53a46371b37b5bd56f`.

## Setup

Prerequisite: Python 3.10 or newer. There are no third-party runtime dependencies.

No runtime environment variables are required. The GitHub Action accepts an optional `github-token` input, used only to raise API rate limits for public read requests.

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
| Redacted environment example or explicit README no-configuration statement | 10 |
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

The fixed-price entry offer is the [$149 Agent-Ready Repo Fix Plan](docs/agent-ready-fix-plan.md). It covers one public repository and exactly three human-reviewed fix cards, delivered publicly on the completed audit issue. It does not include implementation. A [structured public request](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=fix-plan-request.yml) records authorization and scope acknowledgement without collecting payment details. Automated preflight verifies that the audit and repository match; use the dedicated [PayPal goods/services checkout](https://www.paypal.com/ncp/payment/H9VVRGRGA3DCG) only after WrightOps confirms the fixed scope.

The implementation offer is the
[$249 Founding Agent-Ready Instructions PR](docs/agent-ready-instructions-pr.md).
It covers one completed audit or
[no-login repository preflight](https://zachwright.xyz/#preflight), one public
repository and immutable revision, exactly root `AGENTS.md` plus one selected
companion file—root `CLAUDE.md` or `.github/copilot-instructions.md`—one
ready-to-merge pull request, and one revision round. WrightOps manually
revalidates the public repository and immutable revision before confirming
scope, uses only committed public documentation and workflows, and does not
execute target repository code. Its
[public request](https://github.com/wrightops-ai/agent-ready-repo-auditor/issues/new?template=instructions-pr-request.yml)
records the public inputs and authorization; written scope confirmation comes
before the dedicated PayPal Goods & Services checkout is shared privately.
The [merged sample PR](https://github.com/wrightops-ai/bounty-red-flag-card/pull/1)
shows the Copilot companion variant of the promised two-file contribution on
an owned public repository.

## License

MIT
