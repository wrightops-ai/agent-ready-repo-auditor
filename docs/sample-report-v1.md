# Agent-Ready Repository Audit

Repository: [wrightops-ai/agent-ready-repo-auditor](https://github.com/wrightops-ai/agent-ready-repo-auditor)

Immutable revision: `7a507bc0cb42f8c04fb18e53a46371b37b5bd56f` (main)

Evidence score: **90/100 (90%)** — `well_evidenced`

## Checks

| Check | Status | Score | Finding |
| --- | --- | ---: | --- |
| README and setup guidance | `met` | 20/20 | Root README and actionable setup evidence were found. |
| Coding-agent instructions | `met` | 20/20 | A recognized, inspectable coding-agent instruction file was found. |
| Runtime environment configuration | `not_evidenced` | 0/10 | Neither a recognized root environment example nor an explicit no-configuration statement was evidenced. |
| Continuous integration | `met` | 15/15 | At least one GitHub Actions workflow was found. |
| Issue and pull-request templates | `met` | 10/10 | Issue and pull-request templates were found. |
| Verification commands and automation | `met` | 15/15 | Verification files and written verification evidence were found. |
| Risky-action boundaries | `met` | 10/10 | At least one explicit approval or prohibition boundary was evidenced. |

## Evidence

### README and setup guidance

- [README.md](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/README.md): Root README exists.
- [README.md line 3](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/README.md#L3): README includes an executable-looking command.
- [README.md line 36](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/README.md#L36): README includes setup-oriented guidance.

### Coding-agent instructions

- [AGENTS.md](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/AGENTS.md): Recognized coding-agent instruction file exists.

### Runtime environment configuration

- No public evidence recorded.

### Continuous integration

- [.github/workflows/ci.yml](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/workflows/ci.yml): GitHub Actions workflow exists.
- [.github/workflows/fulfill-audit-request.yml](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/workflows/fulfill-audit-request.yml): GitHub Actions workflow exists.

### Issue and pull-request templates

- [.github/ISSUE\_TEMPLATE/audit-request.yml](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/ISSUE_TEMPLATE/audit-request.yml): Issue template exists.
- [.github/ISSUE\_TEMPLATE/config.yml](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/ISSUE_TEMPLATE/config.yml): Issue template exists.
- [.github/pull\_request\_template.md](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/pull_request_template.md): Pull-request template exists.

### Verification commands and automation

- [.github/workflows/ci.yml line 12](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/.github/workflows/ci.yml#L12): Verification-oriented guidance or configuration was found.
- [AGENTS.md line 5](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/AGENTS.md#L5): Verification-oriented guidance or configuration was found.
- [README.md line 9](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/README.md#L9): Verification-oriented guidance or configuration was found.
- [tests/\_\_init\_\_.py](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/tests/__init__.py): Verification-related file or path exists.
- [tests/test\_auditor.py](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/tests/test_auditor.py): Verification-related file or path exists.

### Risky-action boundaries

- [AGENTS.md line 7](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/7a507bc0cb42f8c04fb18e53a46371b37b5bd56f/AGENTS.md#L7): Explicit risky-action boundary language was found.

## Prioritized next steps

1. If runtime configuration is required, add a redacted root .env.example that names it without real secrets; otherwise state explicitly in the root README that no runtime environment configuration is required.

## Inspection limits

- This is an operational coding-agent readiness evidence review, not a vulnerability or security assessment.
- A missing public artifact means only that the auditor did not evidence it in the scanned default-branch snapshot.
- The auditor does not execute repository code, verify documentation accuracy, inspect private settings, or prove production safety.
