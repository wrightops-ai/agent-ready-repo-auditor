from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "human-audit-scope-request.yml"
TERMS = ROOT / "docs" / "agent-ready-repository-audit.md"


class HumanAuditIntakeTests(unittest.TestCase):
    def test_scope_form_is_passive_public_and_payment_gated(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn('title: "[Human audit request] "', text)
        self.assertNotIn("labels:", text)
        self.assertNotIn("paypal.com", text.lower())
        self.assertNotIn("mailto:", text.lower())
        for field_id in (
            "repository",
            "workflow_pain",
            "handoff",
            "authorization",
            "scope",
        ):
            self.assertIn(f"id: {field_id}", text)
        for required_boundary in (
            "does not create a contract or payment obligation",
            "authorized to request a public-evidence review",
            "PayPal Business reports a settled payment",
            "not a vulnerability, security, privacy, legal, or compliance assessment",
            "payment information must never be posted to GitHub",
        ):
            self.assertIn(required_boundary, text)

    def test_public_terms_match_registered_offer_boundary(self) -> None:
        text = TERMS.read_text(encoding="utf-8")

        for required_term in (
            "**$750 USD**",
            "three business days",
            "four hours",
            "One evidence-linked JSON audit",
            "One evidence-linked Markdown audit",
            "up to five repository-specific priorities",
            "30-minute recorded or live handoff",
            "one immutable default-branch revision",
            "does not begin",
            "full purchase price is refundable before work begins",
            "Refund decisions and execution remain owner-confirmed",
        ):
            self.assertIn(required_term, text)
        self.assertNotIn("https://www.paypal.com", text)
        self.assertNotIn("mailto:", text.lower())

    def test_readme_exposes_scope_request_without_direct_checkout(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("template=human-audit-scope-request.yml", text)
        self.assertIn("docs/agent-ready-repository-audit.md", text)


if __name__ == "__main__":
    unittest.main()
