# Owner publication checklist

Every unchecked item is a stop condition. These steps intentionally require an authorized human owner.

## 1. Legal and account gates

- [ ] Read the current [GitHub Marketplace Developer Agreement](https://docs.github.com/en/site-policy/github-terms/github-marketplace-developer-agreement) in full.
- [ ] Read the current [GitHub Marketplace Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-marketplace-terms-of-service) in full.
- [ ] Decide and document whether the MIT `LICENSE` is the intended product EULA. Obtain legal review or add an approved EULA if needed.
- [ ] Confirm the accepting person has authority to bind the `wrightops-ai` repository owner.
- [ ] Confirm two-factor authentication is enabled for the publishing account.
- [ ] Confirm the public GitHub issue tracker is an acceptable ongoing support channel.

Do not delegate agreement acceptance, EULA approval, identity verification, or 2FA to an automation agent.

## 2. Release-candidate verification

- [ ] Review `marketplace/README.md` and `marketplace/listing-copy.md` against the current official GitHub documentation.
- [ ] Confirm the working tree is clean and the intended commit is pushed to `main`.
- [ ] Confirm the full test, compile, lint, typing, YAML, and local Action consumer checks pass on that exact commit.
- [ ] Confirm hosted CI is green, including `Local action consumer`.
- [ ] Confirm `action.yml` still contains the approved name, description, branding, inputs, outputs, and composite runtime.
- [ ] Confirm the root README's installation example and limitations remain accurate.
- [ ] Confirm the proposed release contains no credentials, customer data, private artifacts, or unrelated files.

Record the approved release commit SHA here: `________________________________________`

## 3. GitHub release flow

GitHub's documented path is through the repository's root `action.yml` page:

1. Open [`action.yml`](https://github.com/wrightops-ai/agent-ready-repo-auditor/blob/main/action.yml).
2. Click **Draft a release** in the Marketplace banner.
3. If GitHub requires acceptance of the Marketplace Developer Agreement, stop and complete that owner-only review deliberately.
4. Select **Publish this Action to the GitHub Marketplace**.
5. Require the metadata validator to show **Everything looks good!**
6. If GitHub reports a name collision, reserved name, category conflict, or metadata warning, stop. Do not publish around the validator.
7. Select `Continuous integration` as the primary category.
8. Select `Code quality` as the secondary category.
9. Create the approved semantic tag, suggested `v1.1.1`, from the recorded release SHA. Never move or recreate an immutable semantic tag.
10. Use the title and notes in `marketplace/listing-copy.md`, updated for the final version.
11. Review the complete release preview, including the exact tag, categories, public README content, and Marketplace checkbox.
12. Click **Publish release** only when ready for immediate public listing. GitHub requires 2FA for this action.

The exact-name search returned no listing on 2026-07-16, but only the release-page validator is authoritative.

## 4. Floating major tag decision

- [ ] Decide whether the existing floating `v1` tag should advance to the new release, consistent with the repository's immutable-release policy.
- [ ] If advancing it, verify `wrightops-ai/agent-ready-repo-auditor@v1` in a clean consumer workflow after the update.
- [ ] Never force-move `v1.1.0`, `v1.1.1`, or another immutable semantic release tag.

## 5. Post-publication verification

- [ ] Open the public Marketplace listing and confirm the name, description, author, icon, categories, version, README, license, and limitations render correctly.
- [ ] Confirm the Marketplace installation snippet uses the intended owner, repository, and version.
- [ ] Run the Action from a clean public test repository using both the semantic version and intended floating major tag.
- [ ] Confirm all declared outputs are populated and the generated report links to an immutable revision.
- [ ] Confirm the support link opens the correct public issue tracker.
- [ ] Add the Marketplace listing URL and publication date to the business asset register.
- [ ] Monitor the first installations and support requests without sending unsolicited commercial messages.

Record the listing URL here: `________________________________________`

Record the publication date here: `________________________________________`
