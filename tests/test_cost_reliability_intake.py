from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "cost-reliability-snapshot-request.yml"
TERMS = ROOT / "docs" / "ai-agent-cost-reliability-snapshot.md"
README = ROOT / "README.md"


class CostReliabilityIntakeTests(unittest.TestCase):
    def test_scope_form_is_public_passive_and_prompt_free(self) -> None:
        text = TEMPLATE.read_text(encoding="utf-8")
        for marker in (
            "$495 AI Agent Cost & Reliability Snapshot",
            "does not create a contract or payment obligation",
            "Pseudonymous workflow label",
            "Primary decision",
            "Normalized evidence readiness",
            "Private transfer is arranged only after written scope confirmation",
            "one workflow, up to 20 pseudonymous task IDs and 50 normalized attempts",
            "three business days",
            "settled payment",
            "not causal attribution",
            "complete $495 Snapshot terms",
        ):
            self.assertIn(marker, text)

        for forbidden in (
            "mailto:",
            "paypal.com/ncp/payment",
            "labels:",
            "assignees:",
            "contact email",
        ):
            self.assertNotIn(forbidden, text.lower())

    def test_terms_define_acceptance_exclusions_and_refund_boundary(self) -> None:
        text = TERMS.read_text(encoding="utf-8")
        for marker in (
            "**$495 USD**",
            "one workflow, up to 20 pseudonymous task IDs and 50 normalized attempts",
            "deterministic aggregate JSON report",
            "matching human-readable Markdown scorecard",
            "normalized input SHA-256",
            "Missing primary evidence remains explicitly unavailable",
            "user-supplied scenario",
            "Do not post run records",
            "The full purchase price is refundable before work begins",
            "PayPal seller fee retained on a required refund",
            "template=cost-reliability-snapshot-request.yml",
        ):
            self.assertIn(marker, text)

    def test_readme_exposes_the_scope_and_terms_without_checkout(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn("AI Agent Cost & Reliability Snapshot", text)
        self.assertIn("template=cost-reliability-snapshot-request.yml", text)
        self.assertIn("docs/ai-agent-cost-reliability-snapshot.md", text)
        self.assertNotIn("payment/495", text)


if __name__ == "__main__":
    unittest.main()
