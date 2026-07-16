# Marketplace listing copy

This file is a paste-ready owner handoff. It does not authorize publication.

## Release fields

- **Suggested tag:** `v1.1.1`
- **Suggested title:** `Agent-Ready Repository Audit v1.1.1`
- **Primary category:** `Continuous integration`
- **Secondary category:** `Code quality`
- **Publish this Action to GitHub Marketplace:** owner selects only after completing every gate in `owner-publication-checklist.md`

The suggested patch release is documentation/readiness-only and should target the reviewed commit containing this package. If the owner chooses a different version, update all references before publishing.

## Draft release notes

```markdown
## Agent-Ready Repository Audit v1.1.1

Marketplace publication release for the dependency-free public-evidence auditor.

### What it does

- Scores repository setup, coding-agent instructions, environment guidance, CI, contribution templates, verification, and risky-action boundaries.
- Links every positive finding to an immutable public GitHub revision.
- Writes deterministic Markdown or JSON without cloning or executing repository code.
- Exposes `score`, `band`, `report-path`, and `revision` outputs for CI policy gates.

### Safety and scope

This is an operational coding-agent readiness evidence review. It is not a vulnerability scanner, security assessment, privacy review, legal review, compliance review, or proof that documentation is accurate.

Runtime behavior is unchanged from v1.1.0; this patch adds Marketplace readiness documentation.
```

## Listing claim guardrails

Use:

- “Audits public GitHub evidence for coding-agent operational readiness.”
- “Does not clone or execute repository code.”
- “Deterministic Markdown and JSON with immutable evidence links.”
- “Works with Codex, Claude Code, GitHub Copilot coding agent, Cursor, and mixed-agent workflows.”

Do not use:

- “Secures your repository.”
- “Proves your repository is agent-safe.”
- “Finds vulnerabilities.”
- “Guarantees agent success.”
- “Compliance-ready” or similar unmeasured outcome claims.

## Public support response

```markdown
For installation questions or reproducible bugs, open a public issue with a minimal public example. Do not include secrets, credentials, private repository details, or personal data. This project cannot review sensitive reports in a public issue.
```
