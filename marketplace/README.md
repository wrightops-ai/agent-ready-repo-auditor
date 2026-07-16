# GitHub Marketplace readiness

Status snapshot: **technically ready; owner and legal gates remain open**  
Verified: **2026-07-16**  
Target: free GitHub Action listing for `wrightops-ai/agent-ready-repo-auditor`

This package prepares the repository for publication without accepting agreements, creating a release, selecting Marketplace categories, or changing any external state. GitHub publishes qualifying Actions immediately after the owner completes the release flow, so the final controls intentionally remain manual.

## Readiness decision

The current repository satisfies the locally verifiable Action metadata and repository-shape requirements. Publication must not proceed until an authorized owner:

1. reviews and accepts the GitHub Marketplace Developer Agreement and related terms;
2. confirms what document will serve as the product EULA;
3. confirms two-factor authentication is enabled for the publishing account;
4. passes GitHub's live release-page validation, including the authoritative name-uniqueness check; and
5. deliberately publishes a release with the Marketplace checkbox selected.

The existing MIT `LICENSE` grants end-user rights, but this package does **not** make a legal determination that it satisfies the Developer Agreement's separate-EULA requirement. That is an owner/legal decision.

## Requirement audit

| Requirement | Status | Current evidence | Remaining action |
| --- | --- | --- | --- |
| Public repository | Pass | GitHub reports `wrightops-ai/agent-ready-repo-auditor` as public. | Reconfirm immediately before publication. |
| One root Action metadata file | Pass | The repository contains one root `action.yml` and no other `action.yml` or `action.yaml`. | Keep the filename stable across releases. |
| Required Action metadata | Pass | `action.yml` has `name`, `description`, and composite `runs`; every input has a description; every composite output maps a `value`. | Confirm GitHub shows “Everything looks good!” in the release UI. |
| Supported branding | Pass | `check-circle` is a supported Feather icon and `blue` is a supported badge color. | None. |
| Unique Marketplace name | Provisional pass | An exact Marketplace search for `Agent-Ready Repository Audit` returned zero results on 2026-07-16. | Treat the release UI validator as authoritative because search indexing can lag. |
| Name is not an owner, category, or obvious reserved feature name | Pass with live recheck | The name differs from `wrightops-ai`, `WrightOps AI`, and current Marketplace category names. | Stop if the release UI warns about a reserved or conflicting name. |
| Action-specific repository | Pass with owner review | The repository contains the Action runtime, its dependency-free library/CLI, tests, documentation, and closely related free-audit automation; no unrelated product bundle was found. | Owner should confirm the free-audit automation remains in scope for this product. |
| Installation and usage guidance | Pass | The root README includes an `@v1` workflow example, inputs/outputs, limitations, tests, and a sample report. | Keep claims synchronized with runtime behavior. |
| Support path | Pass | The public issue tracker is the non-sensitive support and feedback channel. The request form warns against secrets and private data. | Owner should verify this support commitment is sustainable. |
| Semantic release | Pass | Public releases `v1` and `v1.1.0` exist; `v1.1.0` is latest. | Use a reviewed semantic release for Marketplace publication. Never rewrite an immutable semantic tag. |
| License/EULA | Owner/legal gate | MIT `LICENSE` exists. The Developer Agreement states that a separate EULA must govern end-user rights. | Owner/legal reviewer must document whether MIT is the intended EULA or add an approved EULA before acceptance. |
| Marketplace Developer Agreement | Owner-only gate | Not accepted or checked by this package. | Organization owner reads and accepts it in GitHub's release flow. |
| Two-factor authentication | Owner-only gate | Not inspected. | Publishing account confirms 2FA before pressing Publish release. |

## Product-policy notes

- The proposed listing is free. Marketplace publication is a distribution and acquisition channel, not the payment rail for human-reviewed remediation.
- The Action makes bounded read requests directly from the user's runner to `api.github.com`. It does not send repository contents or telemetry to a WrightOps-operated service.
- The Action audits public evidence deterministically and does not call a generative-AI model. Therefore, the Developer Agreement's generative-AI interaction requirements appear inapplicable; this is an inference, not a legal conclusion.
- The Action must continue to avoid unsolicited commercial messages. Its remediation-interest flow is user-initiated and non-binding.
- Marketing text must continue to describe an operational evidence audit—not a security, privacy, legal, compliance, or vulnerability assessment.

## Recommended Marketplace positioning

- **Name:** `Agent-Ready Repository Audit`
- **Description:** use the exact `description` in `action.yml`
- **Primary category:** `Continuous integration`
- **Secondary category:** `Code quality`
- **Pricing:** free Action
- **Support:** public GitHub issues for non-sensitive questions

`Continuous integration` is the best primary fit because the product is a repeatable workflow gate with a configurable failure threshold. `Code quality` is a useful secondary discovery category, but the listing must not imply source-code quality or security scanning.

## Verification commands

Run these from the repository root before handing the release to the owner:

```bash
find . -type f \( -name action.yml -o -name action.yaml \) -print
ruby -e 'require "yaml"; YAML.load_file("action.yml"); puts "action.yml parses"'
python3 -m unittest discover -v
python3 -m py_compile agent_ready_repo_auditor/*.py scripts/*.py tests/*.py action_entrypoint.py
ruff check .
mypy .
git diff --check
```

The hosted `Local action consumer` CI job should also be green on the exact commit selected for release.

## Current official references

- [Publishing actions in GitHub Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
- [Action metadata syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax)
- [Releasing and maintaining actions](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/release-and-maintain-actions)
- [GitHub Marketplace Developer Agreement](https://docs.github.com/en/site-policy/github-terms/github-marketplace-developer-agreement)
- [GitHub Marketplace Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-marketplace-terms-of-service)
- [Exact-name Marketplace search](https://github.com/marketplace?type=actions&query=Agent-Ready%20Repository%20Audit)

Requirements and terms can change. Reopen these sources on publication day rather than relying only on this dated snapshot.
