# Sample Agent-Ready Repo Fix Plan

> **Demonstration only — not paid, commissioned, or endorsed by Anthropic.**
> WrightOps did not contact the project or submit these changes.
>
> Repository: [`anthropics/claude-code`](https://github.com/anthropics/claude-code)
> at immutable revision
> [`c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab`](https://github.com/anthropics/claude-code/tree/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab).
> Audit evidence was read through the public GitHub API without cloning or
> executing repository code.

The automated evidence score at this revision was 40/100. That score describes
only the seven public artifacts checked by this tool. It is not a product
quality, security, compliance, or maintainability score.

This sample intentionally contains exactly three fix cards, matching the paid
offer. It prioritizes useful public-repository operating gaps; it does not claim
that the project should accept the proposed changes.

## Fix card 1 — Add repository-specific agent instructions

- **Evidenced gap:** No recognized root coding-agent instruction file was
  evidenced in the
  [pinned root tree](https://github.com/anthropics/claude-code/tree/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab).
- **Change location:** `AGENTS.md`
- **Bounded change outline:** Add a short root instruction file that names the
  public repository's purpose, the directories an agent may edit, the source of
  contribution guidance, the verification commands that are actually supported
  in this public checkout, and the escalation path when required source or
  credentials are unavailable. Keep product-internal or private build details
  out of the file.
- **Acceptance check:** At the next immutable revision, `AGENTS.md` exists at
  the repository root, contains repository-specific instructions, and does not
  include credentials, private URLs, or unverifiable commands.
- **Limitations / risky-action boundary:** A public instruction file cannot
  describe private build systems or grant authority. Unknown internal
  procedures must remain unknown.

## Fix card 2 — State the public checkout's configuration boundary

- **Evidenced gap:** The
  [pinned README](https://github.com/anthropics/claude-code/blob/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab/README.md)
  provides installation guidance, but the audit did not evidence a recognized
  root environment example or an explicit statement that no public-checkout
  runtime configuration is required.
- **Change location:** `README.md`
- **Bounded change outline:** Add a "Public repository configuration" note that
  clearly distinguishes end-user authentication from contributor/runtime
  configuration. If public development requires environment variables, name
  only the variable keys and safe placeholder shapes in a redacted root
  `.env.example`; otherwise state that no runtime environment configuration is
  required for the documented public-repository workflow.
- **Acceptance check:** The next pinned audit evidences either a redacted root
  `.env.example` or an explicit no-runtime-configuration statement in the root
  README. No real token, account identifier, customer value, or private endpoint
  appears.
- **Limitations / risky-action boundary:** The wording must be verified by a
  maintainer. The current public evidence is insufficient to choose between the
  two truthful branches.

## Fix card 3 — Define approval gates for risky actions

- **Evidenced gap:** The auditor did not evidence an explicit public approval or
  prohibition boundary for destructive, deployment, credential, publishing, or
  payment actions in the
  [pinned root guidance](https://github.com/anthropics/claude-code/tree/c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab).
- **Change location:** `AGENTS.md`
- **Bounded change outline:** Add a concise "Do not perform without maintainer
  authorization" section covering destructive git operations, release or
  package publication, production/deployment changes, secret or credential
  access, external communications, and financial actions. State that agents
  must stop when a required private system or authority is unavailable.
- **Acceptance check:** The next pinned audit links to explicit approval or
  prohibition language tied to at least one risky-action class, and the file
  does not imply that an automated agent has maintainer or financial authority.
- **Limitations / risky-action boundary:** These are operating guardrails, not
  evidence that the repository or product is secure.

## Delivery check

- Exactly three fix cards: **pass**
- Immutable public revision and source links: **pass**
- Exact change path and acceptance check on every card: **pass**
- Missing evidence preserved as missing: **pass**
- Private data, credentials, and payment identifiers absent: **pass**
- Security, compliance, endorsement, or guaranteed-outcome claim absent:
  **pass**

